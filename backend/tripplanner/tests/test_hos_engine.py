from datetime import timedelta
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from tripplanner.services.hos_engine import (
    CYCLE_LIMIT,
    DRIVING_LIMIT,
    RESET_DURATION,
    RESTART_DURATION,
    simulate_hos,
)
from tripplanner.services.log_builder import build_daily_logs, build_timeline
from tripplanner.services.route_engine import GeoPoint, RouteLeg, RouteResult


def _make_route(
    distance_miles: float,
    drive_hours: float,
    *,
    with_deadhead: bool = False,
) -> RouteResult:
    current = GeoPoint(32.7767, -96.7970, "Dallas, TX")
    pickup = GeoPoint(32.7767, -96.7970, "Dallas, TX")
    dropoff = GeoPoint(39.7392, -104.9903, "Denver, CO")
    polyline = [[-96.7970, 32.7767], [-104.9903, 39.7392]]

    if with_deadhead:
        deadhead = RouteLeg(current, pickup, 50, 1, polyline[:1])
        loaded = RouteLeg(pickup, dropoff, distance_miles - 50, drive_hours - 1, polyline)
        return RouteResult(
            total_distance_miles=distance_miles,
            total_drive_duration_hours=drive_hours,
            polyline=polyline,
            legs=[deadhead, loaded],
            points={"current": current, "pickup": pickup, "dropoff": dropoff},
        )

    loaded = RouteLeg(pickup, dropoff, distance_miles, drive_hours, polyline)
    return RouteResult(
        total_distance_miles=distance_miles,
        total_drive_duration_hours=drive_hours,
        polyline=polyline,
        legs=[loaded],
        points={"current": current, "pickup": pickup, "dropoff": dropoff},
    )


class HOSEngineTests(SimpleTestCase):
    def test_single_day_trip_fits_one_duty_period(self):
        route = _make_route(500, 9)
        result = simulate_hos(route, 0)
        driving = sum(e.duration_hours for e in result.events if e.status == "driving")
        self.assertAlmostEqual(driving, 9, places=1)
        self.assertFalse(result.requires_restart)

    def test_long_trip_requires_ten_hour_reset(self):
        route = _make_route(800, 14)
        result = simulate_hos(route, 0)
        rest_events = [e for e in result.events if e.stop_type == "rest"]
        self.assertTrue(any(e.duration_hours >= RESET_DURATION for e in rest_events))

    def test_cycle_at_limit_returns_restart_only(self):
        route = _make_route(500, 9)
        result = simulate_hos(route, CYCLE_LIMIT)
        self.assertTrue(result.requires_restart)
        self.assertEqual(len(result.events), 1)
        self.assertEqual(result.events[0].duration_hours, RESTART_DURATION)

    def test_high_cycle_forces_thirty_four_hour_restart(self):
        route = _make_route(1200, 18)
        result = simulate_hos(route, 65)
        restart_events = [e for e in result.events if e.stop_type == "restart"]
        self.assertTrue(restart_events)

    def test_driving_respects_eleven_hour_limit_per_period(self):
        route = _make_route(2000, 30)
        result = simulate_hos(route, 0)
        driving_since_reset = 0.0
        for event in result.events:
            if event.status in {"off_duty"} and event.duration_hours >= RESET_DURATION:
                driving_since_reset = 0.0
            elif event.status == "driving":
                driving_since_reset += event.duration_hours
                self.assertLessEqual(driving_since_reset, DRIVING_LIMIT + 0.01)


class LogBuilderTests(SimpleTestCase):
    def test_daily_totals_sum_to_twenty_four_hours(self):
        route = _make_route(800, 14)
        result = simulate_hos(route, 0)
        timed = build_timeline(result.events)
        logs = build_daily_logs(timed)
        for day in logs:
            total = sum(day["totals"].values())
            self.assertAlmostEqual(total, 24.0, places=1, msg=f"Day {day['day_index']} totals={day['totals']}")


class PlanTripAPITests(APITestCase):
    @patch("tripplanner.views.build_route")
    def test_validation_error(self, mock_build_route):
        url = reverse("plan-trip")
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_build_route.assert_not_called()

    @patch("tripplanner.views.build_route")
    def test_cycle_seventy_returns_restart_plan(self, mock_build_route):
        mock_build_route.return_value = _make_route(500, 9)
        url = reverse("plan-trip")
        response = self.client.post(
            url,
            {
                "current_location": "Dallas, TX",
                "pickup_location": "Dallas, TX",
                "dropoff_location": "Denver, CO",
                "current_cycle_used_hours": 70,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["requires_restart"])
