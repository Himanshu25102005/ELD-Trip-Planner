"""Fuel stop placement helpers."""

FUEL_INTERVAL_MILES = 1000
FUEL_STOP_DURATION_HOURS = 0.5


def miles_until_next_fuel(miles_since_last_fuel: float) -> float:
    return max(0.0, FUEL_INTERVAL_MILES - miles_since_last_fuel)


def needs_fuel_before(miles_since_last_fuel: float, proposed_miles: float) -> bool:
    return miles_since_last_fuel + proposed_miles >= FUEL_INTERVAL_MILES
