"""Build dated timelines and per-day FMCSA log sheet structures."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Optional

from django.utils import timezone

from .hos_engine import SimEvent


STATUS_ORDER = ["off_duty", "sleeper_berth", "driving", "on_duty"]


@dataclass
class TimedEvent:
    status: str
    start: datetime
    end: datetime
    location_label: str = ""
    lat: Optional[float] = None
    lng: Optional[float] = None
    stop_type: Optional[str] = None


def _hours_to_hhmm(dt: datetime) -> str:
    return dt.strftime("%H:%M")


def _assign_timestamps(events: list[SimEvent], trip_start: datetime) -> list[TimedEvent]:
    timed: list[TimedEvent] = []
    cursor = trip_start
    for event in events:
        end = cursor + timedelta(hours=event.duration_hours)
        timed.append(
            TimedEvent(
                status=event.status,
                start=cursor,
                end=end,
                location_label=event.location_label,
                lat=event.lat,
                lng=event.lng,
                stop_type=event.stop_type,
            )
        )
        cursor = end
    return timed


def _split_event_at_midnight(event: TimedEvent) -> list[timedelta]:
    """Return segments as (start, end) datetimes within single days."""
    segments: list[tuple[datetime, datetime]] = []
    cursor = event.start
    while cursor < event.end:
        day_end = datetime.combine(cursor.date(), datetime.max.time(), tzinfo=cursor.tzinfo).replace(
            hour=23, minute=59, second=59, microsecond=999999
        )
        if day_end >= event.end:
            segments.append((cursor, event.end))
            break
        next_midnight = datetime.combine(
            cursor.date() + timedelta(days=1),
            datetime.min.time(),
            tzinfo=cursor.tzinfo,
        )
        segments.append((cursor, next_midnight))
        cursor = next_midnight
    return segments


def _duration_hours(start: datetime, end: datetime) -> float:
    return (end - start).total_seconds() / 3600


def build_timeline(events: list[SimEvent], trip_start: Optional[datetime] = None) -> list[TimedEvent]:
    start = trip_start or timezone.now()
    if timezone.is_naive(start):
        start = timezone.make_aware(start, timezone.get_current_timezone())
    return _assign_timestamps(events, start)


def build_daily_logs(timed_events: list[TimedEvent]) -> list[dict[str, Any]]:
    if not timed_events:
        return []

    first_day = timed_events[0].start.date()
    last_day = timed_events[-1].end.date()
    day_count = (last_day - first_day).days + 1

    logs: list[dict[str, Any]] = []

    for day_index in range(day_count):
        current_date = first_day + timedelta(days=day_index)
        day_start = datetime.combine(current_date, datetime.min.time(), tzinfo=timed_events[0].start.tzinfo)
        day_end = day_start + timedelta(days=1)

        day_events: list[dict[str, Any]] = []

        for event in timed_events:
            if event.end <= day_start or event.start >= day_end:
                continue

            seg_start = max(event.start, day_start)
            seg_end = min(event.end, day_end)
            if seg_end <= seg_start:
                continue

            day_events.append(
                {
                    "status": event.status,
                    "start": _hours_to_hhmm(seg_start),
                    "end": _hours_to_hhmm(seg_end),
                    "location_label": event.location_label if seg_start == event.start else "",
                }
            )

        day_events = _fill_gaps(day_events, day_start)
        totals = _compute_totals(day_events, day_start)
        logs.append(
            {
                "day_index": day_index + 1,
                "date": current_date.isoformat(),
                "events": day_events,
                "totals": totals,
            }
        )

    return logs


def _fill_gaps(events: list[dict[str, Any]], day_start: datetime) -> list[dict[str, Any]]:
    if not events:
        return [
            {
                "status": "off_duty",
                "start": "00:00",
                "end": "23:59",
                "location_label": "",
            }
        ]

    events = sorted(events, key=lambda e: e["start"])
    filled: list[dict[str, Any]] = []
    cursor = day_start

    for event in events:
        ev_start = _parse_day_time(day_start, event["start"])
        ev_end = _parse_day_time(day_start, event["end"])
        if ev_end <= ev_start:
            ev_end = ev_end + timedelta(days=1)

        if ev_start > cursor:
            filled.append(
                {
                    "status": "off_duty",
                    "start": _hours_to_hhmm(cursor),
                    "end": _hours_to_hhmm(ev_start),
                    "location_label": "",
                }
            )
        filled.append(event)
        cursor = max(cursor, ev_end)

    day_end = day_start + timedelta(hours=23, minutes=59)
    if cursor < day_end:
        filled.append(
            {
                "status": "off_duty",
                "start": _hours_to_hhmm(cursor),
                "end": "23:59",
                "location_label": "",
            }
        )

    return filled


def _parse_day_time(day_start: datetime, hhmm: str) -> datetime:
    hour, minute = map(int, hhmm.split(":"))
    return day_start.replace(hour=hour, minute=minute, second=0, microsecond=0)


def _compute_totals(events: list[dict[str, Any]], day_start: datetime) -> dict[str, float]:
    totals = {status: 0.0 for status in STATUS_ORDER}
    for event in events:
        start = _parse_day_time(day_start, event["start"])
        end = _parse_day_time(day_start, event["end"])
        if end <= start:
            end += timedelta(days=1)
        totals[event["status"]] += _duration_hours(start, end)

    return {
        "off_duty_hours": round(totals["off_duty"], 2),
        "sleeper_berth_hours": round(totals["sleeper_berth"], 2),
        "driving_hours": round(totals["driving"], 2),
        "on_duty_hours": round(totals["on_duty"], 2),
    }


def build_stops(timed_events: list[TimedEvent]) -> list[dict[str, Any]]:
    stops: list[dict[str, Any]] = []
    for event in timed_events:
        if event.stop_type in {"pickup", "dropoff", "fuel", "rest", "restart"} and event.lat and event.lng:
            stop_type = "rest" if event.stop_type in {"rest", "restart"} else event.stop_type
            if event.stop_type == "restart":
                stop_type = "rest"
            stops.append(
                {
                    "type": stop_type if stop_type in {"pickup", "dropoff", "fuel", "rest"} else "rest",
                    "label": event.location_label,
                    "lat": event.lat,
                    "lng": event.lng,
                    "arrival_time": event.start.isoformat(),
                    "departure_time": event.end.isoformat(),
                }
            )
    return stops


def build_summary(timed_events: list[TimedEvent], stops: list[dict[str, Any]]) -> dict[str, Any]:
    fuel_stops = sum(1 for s in stops if s["type"] == "fuel")
    rest_stops = sum(1 for s in stops if s["type"] == "rest")
    logs_day_count = 0
    if timed_events:
        first_day = timed_events[0].start.date()
        last_day = timed_events[-1].end.date()
        logs_day_count = (last_day - first_day).days + 1

    return {
        "total_days": logs_day_count,
        "total_fuel_stops": fuel_stops,
        "total_rest_stops": rest_stops,
        "trip_start": timed_events[0].start.isoformat() if timed_events else None,
        "trip_end": timed_events[-1].end.isoformat() if timed_events else None,
    }


def assemble_trip_plan(
    route_data: dict[str, Any],
    events: list[SimEvent],
    requires_restart: bool,
    trip_start: Optional[datetime] = None,
) -> dict[str, Any]:
    timed = build_timeline(events, trip_start)
    stops = build_stops(timed)
    logs = build_daily_logs(timed)
    summary = build_summary(timed, stops)

    return {
        "requires_restart": requires_restart,
        "route": {
            **route_data,
            "stops": stops,
        },
        "summary": summary,
        "logs": logs,
    }
