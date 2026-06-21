from datetime import timedelta
from unittest.mock import patch

from django.test import SimpleTestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from tripplanner.services.hos_engine import CYCLE_LIMIT, DRIVING_LIMIT, simulate_hos
from tripplanner.services.log_builder import build_timeline
from tripplanner.services.plan_enrichment import (
    audit_compliance,
    build_duty_periods,
    enrich_trip_plan,
)
from tripplanner.services.route_engine import GeoPoint, RouteLeg, RouteResult


def _make_route(distance_miles: float, drive_hours: float) -> RouteResult:
    current = GeoPoint(32.7767, -96.7970, "Dallas, TX")
    pickup = GeoPoint(32.7767, -96.7970, "Dallas, TX")
    dropoff = GeoPoint(39.7392, -104.9903, "Denver, CO")
    polyline = [[-96.7970, 32.7767], [-104.9903, 39.7392]]
    loaded = RouteLeg(pickup, dropoff, distance_miles, drive_hours, polyline)
    return RouteResult(
        total_distance_miles=distance_miles,
        total_drive_duration_hours=drive_hours,
        polyline=polyline,
        legs=[loaded],
        points={"current": current, "pickup": pickup, "dropoff": dropoff},
    )


class EnrichmentTests(SimpleTestCase):
    def test_duty_periods_respect_eleven_hour_limit(self):
        route = _make_route(800, 14)
        hos = simulate_hos(route, 0)
        timed = build_timeline(hos.events, timezone.now())
        periods = build_duty_periods(timed)
        self.assertTrue(len(periods) >= 1)
        for period in periods:
            self.assertLessEqual(period["driving_hours"], DRIVING_LIMIT + 0.01)

    def test_compliance_audit_passes_for_normal_trip(self):
        route = _make_route(500, 9)
        hos = simulate_hos(route, 0)
        timed = build_timeline(hos.events, timezone.now())
        result = audit_compliance(hos.events, timed, 0, False)
        self.assertTrue(result["compliant"])
        self.assertEqual(result["status"], "COMPLIANT")
        self.assertEqual(result["checks_passed"], result["checks_total"])

    def test_enriched_plan_includes_new_sections(self):
        route = _make_route(500, 9)
        hos = simulate_hos(route, 0)
        timed = build_timeline(hos.events, timezone.now())
        plan = {
            "requires_restart": False,
            "route": {
                "total_distance_miles": 500,
                "total_drive_duration_hours": 9,
                "polyline": [],
                "stops": [],
            },
            "summary": {},
            "logs": [],
        }
        enriched = enrich_trip_plan(plan, hos.events, timed, 10, False)
        for key in ("timeline", "duty_periods", "compliance", "hos_explanations", "stop_details", "reviewer"):
            self.assertIn(key, enriched)


class PlanTripAPITests(APITestCase):
    @patch("tripplanner.views.build_route")
    def test_enriched_fields_in_response(self, mock_build_route):
        mock_build_route.return_value = _make_route(500, 9)
        response = self.client.post(
            "/api/plan-trip/",
            {
                "current_location": "Dallas, TX",
                "pickup_location": "Dallas, TX",
                "dropoff_location": "Denver, CO",
                "current_cycle_used_hours": 10,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("compliance", response.data)
        self.assertIn("duty_periods", response.data)
        self.assertIn("timeline", response.data)
        self.assertIn("reviewer", response.data)
