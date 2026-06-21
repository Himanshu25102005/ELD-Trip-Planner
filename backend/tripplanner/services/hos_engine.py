"""Core FMCSA Hours-of-Service simulation engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .fuel_engine import FUEL_STOP_DURATION_HOURS, miles_until_next_fuel, needs_fuel_before
from .route_engine import RouteResult, point_at_distance_miles


DRIVING_LIMIT = 11.0
WINDOW_LIMIT = 14.0
BREAK_AFTER_DRIVE = 8.0
BREAK_DURATION = 0.5
RESET_DURATION = 10.0
RESTART_DURATION = 34.0
CYCLE_LIMIT = 70.0
PICKUP_DURATION = 1.0
DROPOFF_DURATION = 1.0


@dataclass
class SimEvent:
    status: str
    duration_hours: float
    location_label: str = ""
    lat: Optional[float] = None
    lng: Optional[float] = None
    stop_type: Optional[str] = None


@dataclass
class HOSSimulationResult:
    events: list[SimEvent] = field(default_factory=list)
    requires_restart: bool = False


def _location_at_distance(
    route: RouteResult,
    distance_miles: float,
) -> tuple[float, float, str]:
    lat, lng = point_at_distance_miles(
        route.polyline,
        distance_miles,
        route.total_distance_miles,
    )
    label = f"Mile {distance_miles:.0f}"
    if distance_miles <= 0.01:
        label = route.points["current"].label
    elif abs(distance_miles - route.total_distance_miles) < 0.5:
        label = route.points["dropoff"].label
    return lat, lng, label


def _add_on_duty_block(
    events: list[SimEvent],
    duration: float,
    label: str,
    lat: float,
    lng: float,
    stop_type: str,
    state: dict,
) -> None:
    events.append(
        SimEvent(
            status="on_duty",
            duration_hours=duration,
            location_label=label,
            lat=lat,
            lng=lng,
            stop_type=stop_type,
        )
    )
    state["elapsed_window"] += duration
    state["cycle_hours"] += duration


def _add_off_duty_reset(
    events: list[SimEvent],
    duration: float,
    route: RouteResult,
    state: dict,
    stop_type: str = "rest",
) -> None:
    lat, lng, label = _location_at_distance(route, state["distance_traveled"])
    events.append(
        SimEvent(
            status="off_duty",
            duration_hours=duration,
            location_label=label,
            lat=lat,
            lng=lng,
            stop_type=stop_type,
        )
    )
    if duration >= RESET_DURATION:
        state["elapsed_drive"] = 0.0
        state["elapsed_window"] = 0.0
        state["drive_since_break"] = 0.0
    if duration >= RESTART_DURATION:
        state["cycle_hours"] = 0.0


def _insert_break_if_needed(events: list[SimEvent], route: RouteResult, state: dict) -> bool:
    if state["drive_since_break"] < BREAK_AFTER_DRIVE:
        return False
    lat, lng, label = _location_at_distance(route, state["distance_traveled"])
    events.append(
        SimEvent(
            status="off_duty",
            duration_hours=BREAK_DURATION,
            location_label=label,
            lat=lat,
            lng=lng,
            stop_type="break",
        )
    )
    state["elapsed_window"] += BREAK_DURATION
    state["drive_since_break"] = 0.0
    return True


def _insert_cycle_restart_if_needed(events: list[SimEvent], route: RouteResult, state: dict) -> bool:
    if state["cycle_hours"] < CYCLE_LIMIT:
        return False
    _add_off_duty_reset(events, RESTART_DURATION, route, state, stop_type="restart")
    state["requires_restart_flag"] = True
    return True


def _max_drive_chunk(state: dict, remaining: float) -> float:
    by_driving = DRIVING_LIMIT - state["elapsed_drive"]
    by_window = WINDOW_LIMIT - state["elapsed_window"]
    by_cycle = CYCLE_LIMIT - state["cycle_hours"]
    return min(by_driving, by_window, by_cycle, remaining)


def _apply_drive_segment(
    events: list[SimEvent],
    route: RouteResult,
    state: dict,
    hours: float,
    mph: float,
) -> float:
    miles = hours * mph
    lat, lng, label = _location_at_distance(route, state["distance_traveled"] + miles / 2)
    events.append(
        SimEvent(
            status="driving",
            duration_hours=hours,
            location_label=label,
            lat=lat,
            lng=lng,
        )
    )
    state["elapsed_drive"] += hours
    state["elapsed_window"] += hours
    state["cycle_hours"] += hours
    state["drive_since_break"] += hours
    state["distance_traveled"] += miles
    state["miles_since_fuel"] += miles
    return hours


def _drive_hours(
    events: list[SimEvent],
    route: RouteResult,
    state: dict,
    hours: float,
    mph: float,
) -> None:
    remaining = hours

    while remaining > 0.0001:
        if _insert_cycle_restart_if_needed(events, route, state):
            continue

        _insert_break_if_needed(events, route, state)

        chunk = _max_drive_chunk(state, remaining)
        chunk_miles = chunk * mph

        if chunk > 0 and needs_fuel_before(state["miles_since_fuel"], chunk_miles):
            miles_before_fuel = miles_until_next_fuel(state["miles_since_fuel"])
            if miles_before_fuel <= 0.0001:
                lat, lng, label = _location_at_distance(route, state["distance_traveled"])
                events.append(
                    SimEvent(
                        status="on_duty",
                        duration_hours=FUEL_STOP_DURATION_HOURS,
                        location_label=f"Fuel stop — {label}",
                        lat=lat,
                        lng=lng,
                        stop_type="fuel",
                    )
                )
                state["elapsed_window"] += FUEL_STOP_DURATION_HOURS
                state["cycle_hours"] += FUEL_STOP_DURATION_HOURS
                state["miles_since_fuel"] = 0.0
                continue

            fuel_hours = miles_before_fuel / mph if mph > 0 else chunk
            fuel_hours = min(fuel_hours, chunk, remaining)
            if fuel_hours <= 0.0001:
                continue
            _apply_drive_segment(events, route, state, fuel_hours, mph)
            remaining -= fuel_hours

            lat, lng, label = _location_at_distance(route, state["distance_traveled"])
            events.append(
                SimEvent(
                    status="on_duty",
                    duration_hours=FUEL_STOP_DURATION_HOURS,
                    location_label=f"Fuel stop — {label}",
                    lat=lat,
                    lng=lng,
                    stop_type="fuel",
                )
            )
            state["elapsed_window"] += FUEL_STOP_DURATION_HOURS
            state["cycle_hours"] += FUEL_STOP_DURATION_HOURS
            state["miles_since_fuel"] = 0.0
            continue

        if chunk <= 0.0001:
            _add_off_duty_reset(events, RESET_DURATION, route, state)
            continue

        applied = min(chunk, remaining)
        _apply_drive_segment(events, route, state, applied, mph)
        remaining -= applied


def _ensure_capacity_for_on_duty(
    events: list[SimEvent],
    route: RouteResult,
    state: dict,
    duration: float,
) -> None:
    while state["elapsed_window"] + duration > WINDOW_LIMIT + 0.0001:
        _add_off_duty_reset(events, RESET_DURATION, route, state)
        if _insert_cycle_restart_if_needed(events, route, state):
            continue


def simulate_hos(
    route: RouteResult,
    current_cycle_used_hours: float,
) -> HOSSimulationResult:
    if current_cycle_used_hours >= CYCLE_LIMIT:
        pickup = route.points["pickup"]
        return HOSSimulationResult(
            events=[
                SimEvent(
                    status="off_duty",
                    duration_hours=RESTART_DURATION,
                    location_label=pickup.label,
                    lat=pickup.lat,
                    lng=pickup.lng,
                    stop_type="restart",
                )
            ],
            requires_restart=True,
        )

    mph = (
        route.total_distance_miles / route.total_drive_duration_hours
        if route.total_drive_duration_hours > 0
        else 55.0
    )

    state = {
        "elapsed_drive": 0.0,
        "elapsed_window": 0.0,
        "cycle_hours": current_cycle_used_hours,
        "drive_since_break": 0.0,
        "miles_since_fuel": 0.0,
        "distance_traveled": 0.0,
        "requires_restart_flag": False,
    }
    events: list[SimEvent] = []
    pickup = route.points["pickup"]
    dropoff = route.points["dropoff"]

    if len(route.legs) > 1:
        _drive_hours(events, route, state, route.legs[0].duration_hours, mph)

    _ensure_capacity_for_on_duty(events, route, state, PICKUP_DURATION)
    _add_on_duty_block(
        events,
        PICKUP_DURATION,
        pickup.label,
        pickup.lat,
        pickup.lng,
        "pickup",
        state,
    )

    loaded_leg = route.legs[-1]
    _drive_hours(events, route, state, loaded_leg.duration_hours, mph)

    _ensure_capacity_for_on_duty(events, route, state, DROPOFF_DURATION)
    if state["cycle_hours"] >= CYCLE_LIMIT:
        _insert_cycle_restart_if_needed(events, route, state)
        _ensure_capacity_for_on_duty(events, route, state, DROPOFF_DURATION)

    _add_on_duty_block(
        events,
        DROPOFF_DURATION,
        dropoff.label,
        dropoff.lat,
        dropoff.lng,
        "dropoff",
        state,
    )

    return HOSSimulationResult(events=events, requires_restart=state["requires_restart_flag"])
