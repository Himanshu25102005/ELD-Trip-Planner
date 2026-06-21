"""Trip plan enrichment: compliance audit, duty periods, explanations, reviewer stats."""

from __future__ import annotations

import re
from typing import Any, Optional

from .fuel_engine import FUEL_INTERVAL_MILES, FUEL_STOP_DURATION_HOURS
from .hos_engine import (
    BREAK_AFTER_DRIVE,
    BREAK_DURATION,
    CYCLE_LIMIT,
    DRIVING_LIMIT,
    RESET_DURATION,
    RESTART_DURATION,
    SimEvent,
    WINDOW_LIMIT,
)
from .log_builder import TimedEvent, _duration_hours


def serialize_timeline(timed_events: list[TimedEvent]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for event in timed_events:
        duration = _duration_hours(event.start, event.end)
        items.append(
            {
                "status": event.status,
                "stop_type": event.stop_type,
                "start": event.start.isoformat(),
                "end": event.end.isoformat(),
                "duration_hours": round(duration, 2),
                "location_label": event.location_label,
                "lat": event.lat,
                "lng": event.lng,
                "title": _event_title(event),
            }
        )
    return items


def _event_title(event: TimedEvent) -> str:
    if event.stop_type == "pickup":
        return "Pickup"
    if event.stop_type == "dropoff":
        return "Delivery Complete"
    if event.stop_type == "fuel":
        return "Fuel Stop"
    if event.stop_type == "break":
        return "Mandatory 30-Minute Break"
    if event.stop_type == "restart":
        return "34-Hour Cycle Restart"
    if event.stop_type == "rest":
        return "Required 10-Hour Rest"
    if event.status == "driving":
        return "Driving"
    if event.status == "on_duty":
        return "On Duty (Not Driving)"
    return "Off Duty"


def build_duty_periods(timed_events: list[TimedEvent]) -> list[dict[str, Any]]:
    if not timed_events:
        return []

    periods: list[dict[str, Any]] = []
    current: Optional[dict[str, Any]] = None

    def start_period(event: TimedEvent) -> dict[str, Any]:
        return {
            "index": len(periods) + 1,
            "start": event.start.isoformat(),
            "end": event.end.isoformat(),
            "driving_hours": 0.0,
            "on_duty_hours": 0.0,
            "off_duty_hours": 0.0,
            "max_driving_hours": DRIVING_LIMIT,
            "max_duty_window_hours": WINDOW_LIMIT,
        }

    def close_period(period: dict[str, Any], end_time) -> None:
        period["end"] = end_time.isoformat()
        period["driving_hours"] = round(period["driving_hours"], 2)
        period["on_duty_hours"] = round(period["on_duty_hours"], 2)
        period["off_duty_hours"] = round(period["off_duty_hours"], 2)
        period["remaining_11_hour_limit"] = round(DRIVING_LIMIT - period["driving_hours"], 2)
        period["remaining_14_hour_window"] = round(
            WINDOW_LIMIT - period["driving_hours"] - period["on_duty_hours"] - period["off_duty_hours"],
            2,
        )
        periods.append(period)

    for event in timed_events:
        duration = _duration_hours(event.start, event.end)
        is_reset = (
            event.status == "off_duty"
            and duration >= RESET_DURATION - 0.01
            and event.stop_type in {"rest", "restart", None}
        )

        if is_reset:
            if current is not None:
                close_period(current, event.start)
                current = None
            continue

        if event.status in {"driving", "on_duty"}:
            if current is None:
                current = start_period(event)
            if event.status == "driving":
                current["driving_hours"] += duration
            else:
                current["on_duty_hours"] += duration
            current["end"] = event.end.isoformat()
        elif current is not None and event.status == "off_duty":
            current["off_duty_hours"] += duration
            current["end"] = event.end.isoformat()

    if current is not None:
        last_end = timed_events[-1].end
        close_period(current, last_end)

    return periods


def audit_compliance(
    events: list[SimEvent],
    timed_events: list[TimedEvent],
    cycle_start: float,
    requires_restart: bool,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    # 11-hour driving per duty period
    driving_ok = True
    driving_detail = "No duty period exceeds 11 hours of driving."
    for period in build_duty_periods(timed_events):
        if period["driving_hours"] > DRIVING_LIMIT + 0.01:
            driving_ok = False
            driving_detail = (
                f"Duty period {period['index']} recorded {period['driving_hours']}h driving "
                f"(limit {DRIVING_LIMIT}h)."
            )
            break
    checks.append(
        {
            "rule": "11-Hour Driving Rule",
            "rule_id": "driving_limit",
            "passed": driving_ok,
            "detail": driving_detail,
        }
    )

    # 14-hour duty window per period (drive + on_duty + short off_duty within period)
    window_ok = True
    window_detail = "No duty period exceeds the 14-hour on-duty window."
    for period in build_duty_periods(timed_events):
        window_used = period["driving_hours"] + period["on_duty_hours"] + period["off_duty_hours"]
        if window_used > WINDOW_LIMIT + 0.01:
            window_ok = False
            window_detail = (
                f"Duty period {period['index']} used {window_used:.1f}h of the "
                f"{WINDOW_LIMIT}-hour duty window."
            )
            break
    checks.append(
        {
            "rule": "14-Hour Duty Window",
            "rule_id": "duty_window",
            "passed": window_ok,
            "detail": window_detail,
        }
    )

    # 30-minute break after 8 hours driving within each duty period
    break_ok = True
    break_detail = "30-minute breaks were applied before exceeding 8 hours of accumulated driving."
    drive_since_break = 0.0
    for event in events:
        if event.status == "driving":
            if drive_since_break + event.duration_hours > BREAK_AFTER_DRIVE + 0.01:
                had_break = False
            drive_since_break += event.duration_hours
        elif event.status == "off_duty" and event.duration_hours >= BREAK_DURATION - 0.01:
            if event.stop_type == "break" or event.duration_hours <= BREAK_DURATION + 0.01:
                drive_since_break = 0.0
                had_break = True
        if event.status == "off_duty" and event.duration_hours >= RESET_DURATION:
            drive_since_break = 0.0

    for period in build_duty_periods(timed_events):
        if period["driving_hours"] > BREAK_AFTER_DRIVE + 0.01:
            period_events = [
                e
                for e in timed_events
                if e.start.isoformat() >= period["start"] and e.end.isoformat() <= period["end"]
            ]
            segment_drive = 0.0
            for pe in period_events:
                if pe.status == "driving":
                    if segment_drive + _duration_hours(pe.start, pe.end) > BREAK_AFTER_DRIVE + 0.01:
                        prior_break = any(
                            x.stop_type == "break"
                            for x in period_events
                            if x.end <= pe.start
                        )
                        if not prior_break and segment_drive >= BREAK_AFTER_DRIVE - 0.01:
                            break_ok = False
                            break_detail = (
                                f"Duty period {period['index']} exceeds 8 hours driving "
                                "without a recorded 30-minute break."
                            )
                    segment_drive += _duration_hours(pe.start, pe.end)
                elif pe.stop_type == "break":
                    segment_drive = 0.0

    checks.append(
        {
            "rule": "30-Minute Break Requirement",
            "rule_id": "break_requirement",
            "passed": break_ok,
            "detail": break_detail,
        }
    )

    # 70-hour cycle
    cycle_hours = cycle_start
    cycle_ok = True
    cycle_detail = f"Rolling cycle started at {cycle_start}h and remained within {CYCLE_LIMIT}h."
    for event in events:
        if event.status in {"driving", "on_duty"}:
            cycle_hours += event.duration_hours
            if cycle_hours > CYCLE_LIMIT + 0.01 and event.stop_type != "restart":
                cycle_ok = False
                cycle_detail = f"Cycle usage reached {cycle_hours:.1f}h before a 34-hour restart."
        if event.stop_type == "restart" or (
            event.status == "off_duty" and event.duration_hours >= RESTART_DURATION - 0.01
        ):
            cycle_hours = 0.0

    if requires_restart and cycle_start >= CYCLE_LIMIT:
        cycle_detail = (
            "Trip begins with 70 cycle hours used; a 34-hour restart is required before driving."
        )
        cycle_ok = True

    checks.append(
        {
            "rule": "70-Hour / 8-Day Cycle",
            "rule_id": "cycle_limit",
            "passed": cycle_ok,
            "detail": cycle_detail,
        }
    )

    # 10-hour resets
    reset_ok = True
    reset_detail = "Required 10-hour off-duty resets were inserted when daily limits were reached."
    period_driving = 0.0
    period_window = 0.0
    for event in events:
        if event.status == "driving":
            period_driving += event.duration_hours
            period_window += event.duration_hours
        elif event.status == "on_duty":
            period_window += event.duration_hours
        elif event.status == "off_duty":
            period_window += event.duration_hours
            if event.duration_hours >= RESET_DURATION - 0.01 and event.stop_type in {"rest", "restart", None}:
                if period_driving > DRIVING_LIMIT + 0.01 or period_window > WINDOW_LIMIT + 0.01:
                    reset_ok = False
                    reset_detail = "A 10-hour reset occurred after limits were already exceeded."
                period_driving = 0.0
                period_window = 0.0

    checks.append(
        {
            "rule": "Required 10-Hour Resets",
            "rule_id": "ten_hour_reset",
            "passed": reset_ok,
            "detail": reset_detail,
        }
    )

    passed_count = sum(1 for c in checks if c["passed"])
    compliant = passed_count == len(checks)

    return {
        "compliant": compliant,
        "status": "COMPLIANT" if compliant else "NON-COMPLIANT",
        "checks_passed": passed_count,
        "checks_total": len(checks),
        "checks": checks,
        "explanation": (
            "This plan was generated by enforcing FMCSA limits per duty period. "
            "Daily log sheets split events at midnight for display; calendar-day driving totals "
            "may exceed 11 hours when a single duty period crosses midnight."
            if compliant
            else "One or more FMCSA rule checks did not pass. Review duty period analysis below."
        ),
    }


def build_hos_explanations(timed_events: list[TimedEvent]) -> list[dict[str, Any]]:
    explanations: list[dict[str, Any]] = []
    fuel_count = 0
    rest_count = 0

    for event in timed_events:
        duration = _duration_hours(event.start, event.end)
        code = event.stop_type or event.status
        message = ""

        if event.stop_type == "pickup":
            message = (
                "A fixed 1-hour on-duty (not driving) block was inserted at pickup "
                "per assessment assumptions."
            )
        elif event.stop_type == "dropoff":
            message = (
                "A fixed 1-hour on-duty (not driving) block was inserted at delivery "
                "per assessment assumptions."
            )
        elif event.stop_type == "fuel":
            fuel_count += 1
            mile = _extract_mile(event.location_label)
            message = (
                f"Fuel stop #{fuel_count} was inserted at approximately mile {mile} "
                f"because the assessment requires refueling at least every {FUEL_INTERVAL_MILES} miles "
                f"({FUEL_STOP_DURATION_HOURS * 60:.0f}-minute on-duty stop)."
            )
        elif event.stop_type == "break":
            message = (
                "A 30-minute off-duty break was inserted after 8 cumulative hours of driving "
                "to satisfy the FMCSA break requirement before additional driving."
            )
        elif event.stop_type == "rest" and duration >= RESET_DURATION - 0.01:
            rest_count += 1
            if duration >= RESTART_DURATION - 0.01:
                message = (
                    "A 34-hour off-duty restart was inserted because the driver reached "
                    "the 70-hour / 8-day cycle limit."
                )
            else:
                message = (
                    f"A 10-hour off-duty reset (rest stop #{rest_count}) was inserted because "
                    "the driver reached the 11-hour driving limit and/or 14-hour duty window "
                    "for the current duty period."
                )
        elif event.stop_type == "restart":
            message = (
                "A 34-hour off-duty restart was required because the trip began with "
                "70 hours already used in the rolling 8-day cycle."
            )
        elif event.status == "driving" and not event.stop_type:
            continue

        if message:
            explanations.append(
                {
                    "code": code,
                    "start": event.start.isoformat(),
                    "end": event.end.isoformat(),
                    "duration_hours": round(duration, 2),
                    "location_label": event.location_label,
                    "message": message,
                }
            )

    return explanations


def build_stop_details(
    timed_events: list[TimedEvent],
    total_distance_miles: float,
) -> dict[str, list[dict[str, Any]]]:
    fuel_stops: list[dict[str, Any]] = []
    rest_stops: list[dict[str, Any]] = []
    fuel_index = 0
    rest_index = 0

    for event in timed_events:
        duration = _duration_hours(event.start, event.end)
        mile = _extract_mile(event.location_label)

        if event.stop_type == "fuel":
            fuel_index += 1
            fuel_stops.append(
                {
                    "index": fuel_index,
                    "type": "fuel",
                    "label": event.location_label,
                    "mile_marker": mile,
                    "arrival_time": event.start.isoformat(),
                    "departure_time": event.end.isoformat(),
                    "duration_hours": round(duration, 2),
                    "duration_minutes": round(duration * 60),
                    "reason": (
                        f"Assessment rule: refuel every {FUEL_INTERVAL_MILES} miles "
                        f"({FUEL_STOP_DURATION_HOURS * 60:.0f}-minute on-duty stop)"
                    ),
                    "lat": event.lat,
                    "lng": event.lng,
                }
            )
        elif event.stop_type in {"rest", "restart"} and duration >= RESET_DURATION - 0.01:
            rest_index += 1
            if duration >= RESTART_DURATION - 0.01:
                rule = "70-Hour / 8-Day Cycle — 34-hour restart"
                reason = "Driver reached the 70-hour rolling cycle limit."
            else:
                rule = "11-Hour Driving / 14-Hour Duty Window — 10-hour reset"
                reason = (
                    "Driver reached the 11-hour driving limit and/or 14-hour duty window "
                    "for the current duty period."
                )
            rest_stops.append(
                {
                    "index": rest_index,
                    "type": "restart" if duration >= RESTART_DURATION - 0.01 else "rest",
                    "label": event.location_label,
                    "mile_marker": mile,
                    "arrival_time": event.start.isoformat(),
                    "departure_time": event.end.isoformat(),
                    "duration_hours": round(duration, 2),
                    "hos_rule_triggered": rule,
                    "reason": reason,
                    "lat": event.lat,
                    "lng": event.lng,
                }
            )

    return {"fuel_stops": fuel_stops, "rest_stops": rest_stops}


def build_reviewer_stats(
    events: list[SimEvent],
    timed_events: list[TimedEvent],
    route_data: dict[str, Any],
    cycle_start: float,
    requires_restart: bool,
) -> dict[str, Any]:
    total_driving = sum(e.duration_hours for e in events if e.status == "driving")
    total_on_duty = sum(e.duration_hours for e in events if e.status == "on_duty")
    total_off_duty = sum(e.duration_hours for e in events if e.status == "off_duty")
    break_count = sum(1 for e in events if e.stop_type == "break")
    ten_hour_resets = sum(
        1
        for e in events
        if e.status == "off_duty"
        and RESET_DURATION - 0.01 <= e.duration_hours < RESTART_DURATION - 0.01
        and e.stop_type in {"rest", None}
    )
    thirty_four_hour_restarts = sum(
        1
        for e in events
        if e.stop_type == "restart"
        or (e.status == "off_duty" and e.duration_hours >= RESTART_DURATION - 0.01)
    )

    cycle_end = cycle_start
    for event in events:
        if event.status in {"driving", "on_duty"}:
            cycle_end += event.duration_hours
        if event.stop_type == "restart" or (
            event.status == "off_duty" and event.duration_hours >= RESTART_DURATION - 0.01
        ):
            cycle_end = 0.0

    duty_periods = build_duty_periods(timed_events)
    trip_duration = 0.0
    if timed_events:
        trip_duration = _duration_hours(timed_events[0].start, timed_events[-1].end)

    stop_details = build_stop_details(timed_events, route_data.get("total_distance_miles", 0))

    return {
        "route_distance_miles": route_data.get("total_distance_miles"),
        "raw_drive_time_hours": route_data.get("total_drive_duration_hours"),
        "total_driving_hours": round(total_driving, 2),
        "total_on_duty_hours": round(total_on_duty, 2),
        "total_off_duty_hours": round(total_off_duty, 2),
        "trip_duration_hours": round(trip_duration, 2),
        "fuel_stop_count": len(stop_details["fuel_stops"]),
        "rest_stop_count": len(stop_details["rest_stops"]),
        "break_count": break_count,
        "duty_period_count": len(duty_periods),
        "ten_hour_reset_count": ten_hour_resets,
        "thirty_four_hour_restart_count": thirty_four_hour_restarts,
        "cycle_hours_at_start": cycle_start,
        "cycle_hours_at_end": round(cycle_end, 2),
        "requires_restart_at_trip_start": requires_restart and cycle_start >= CYCLE_LIMIT,
        "assumptions": [
            {"id": "property_carrying", "label": "Property-carrying driver", "applied": True},
            {"id": "cycle_70_8", "label": "70-hour / 8-day cycle (not 60/7)", "applied": True},
            {"id": "fuel_1000", "label": f"Fuel stop every {FUEL_INTERVAL_MILES} miles", "applied": True},
            {"id": "pickup_1hr", "label": "1-hour on-duty pickup", "applied": True},
            {"id": "dropoff_1hr", "label": "1-hour on-duty dropoff", "applied": True},
            {"id": "no_adverse_weather", "label": "No adverse driving conditions exception", "applied": True},
        ],
    }


def enrich_trip_plan(
    plan: dict[str, Any],
    events: list[SimEvent],
    timed_events: list[TimedEvent],
    cycle_start: float,
    requires_restart: bool,
) -> dict[str, Any]:
    route_data = {
        "total_distance_miles": plan["route"]["total_distance_miles"],
        "total_drive_duration_hours": plan["route"]["total_drive_duration_hours"],
    }

    plan["timeline"] = serialize_timeline(timed_events)
    plan["duty_periods"] = build_duty_periods(timed_events)
    plan["compliance"] = audit_compliance(events, timed_events, cycle_start, requires_restart)
    plan["hos_explanations"] = build_hos_explanations(timed_events)
    plan["stop_details"] = build_stop_details(timed_events, route_data["total_distance_miles"])
    plan["reviewer"] = build_reviewer_stats(
        events, timed_events, route_data, cycle_start, requires_restart
    )
    return plan


def _extract_mile(label: str) -> Optional[int]:
    if not label:
        return None
    match = re.search(r"mile\s*(\d+)", label, re.IGNORECASE)
    if match:
        return int(match.group(1))
    match = re.search(r"Mile\s*(\d+)", label)
    if match:
        return int(match.group(1))
    return None
