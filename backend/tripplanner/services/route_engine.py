"""Geocoding and route retrieval."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import requests
from django.conf import settings


class GeocodingError(Exception):
    def __init__(self, location: str):
        self.location = location
        super().__init__(f"Could not resolve location: {location}")


class RoutingError(Exception):
    pass


@dataclass
class GeoPoint:
    lat: float
    lng: float
    label: str


@dataclass
class RouteLeg:
    start: GeoPoint
    end: GeoPoint
    distance_miles: float
    duration_hours: float
    coordinates: list[list[float]] = field(default_factory=list)


@dataclass
class RouteResult:
    total_distance_miles: float
    total_drive_duration_hours: float
    polyline: list[list[float]]
    legs: list[RouteLeg]
    points: dict[str, GeoPoint]


def normalize_location(value: str) -> str:
    return " ".join(value.strip().lower().split())


def locations_match(a: str, b: str) -> bool:
    return normalize_location(a) == normalize_location(b)


def haversine_miles(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius_miles = 3958.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    x = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius_miles * math.asin(math.sqrt(x))


def geocode(location: str) -> GeoPoint:
    api_key = settings.ORS_API_KEY
    headers = {"User-Agent": "ELD-TripPlanner/1.0"}

    if api_key:
        url = "https://api.openrouteservice.org/geocode/search"
        params = {"api_key": api_key, "text": location, "size": 1}
        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            raise GeocodingError(location)
        features = response.json().get("features", [])
        if not features:
            raise GeocodingError(location)
        coords = features[0]["geometry"]["coordinates"]
        return GeoPoint(lat=coords[1], lng=coords[0], label=location)

    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": location, "format": "json", "limit": 1, "countrycodes": "us"}
    response = requests.get(url, params=params, headers=headers, timeout=15)
    if response.status_code != 200:
        raise GeocodingError(location)
    results = response.json()
    if not results:
        raise GeocodingError(location)
    item = results[0]
    return GeoPoint(lat=float(item["lat"]), lng=float(item["lon"]), label=location)


def _decode_polyline(encoded: str) -> list[list[float]]:
    coordinates: list[list[float]] = []
    index = lat = lng = 0
    while index < len(encoded):
        result = shift = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        dlat = ~(result >> 1) if result & 1 else result >> 1
        lat += dlat

        result = shift = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        dlng = ~(result >> 1) if result & 1 else result >> 1
        lng += dlng
        coordinates.append([lng / 1e5, lat / 1e5])
    return coordinates


def _route_leg(start: GeoPoint, end: GeoPoint) -> RouteLeg:
    api_key = settings.ORS_API_KEY
    headers = {"User-Agent": "ELD-TripPlanner/1.0"}

    if api_key:
        url = "https://api.openrouteservice.org/v2/directions/driving-car"
        params = {"api_key": api_key}
        body = {"coordinates": [[start.lng, start.lat], [end.lng, end.lat]]}
        response = requests.post(url, params=params, json=body, timeout=20)
        if response.status_code != 200:
            raise RoutingError("Route calculation service unavailable, please retry.")
        data = response.json()
        summary = data["routes"][0]["summary"]
        geometry = data["routes"][0]["geometry"]
        if isinstance(geometry, str):
            coords = _decode_polyline(geometry)
        else:
            coords = geometry.get("coordinates", [])
        distance_miles = summary["distance"] / 1609.344
        duration_hours = summary["duration"] / 3600
        return RouteLeg(
            start=start,
            end=end,
            distance_miles=distance_miles,
            duration_hours=duration_hours,
            coordinates=coords,
        )

    url = (
        f"http://router.project-osrm.org/route/v1/driving/"
        f"{start.lng},{start.lat};{end.lng},{end.lat}"
    )
    params = {"overview": "full", "geometries": "geojson"}
    response = requests.get(url, params=params, headers=headers, timeout=20)
    if response.status_code != 200:
        raise RoutingError("Route calculation service unavailable, please retry.")
    payload = response.json()
    if payload.get("code") != "Ok" or not payload.get("routes"):
        raise RoutingError("Route calculation service unavailable, please retry.")
    route = payload["routes"][0]
    coords = route["geometry"]["coordinates"]
    distance_miles = route["distance"] / 1609.344
    duration_hours = route["duration"] / 3600
    return RouteLeg(
        start=start,
        end=end,
        distance_miles=distance_miles,
        duration_hours=duration_hours,
        coordinates=coords,
    )


def build_route(
    current_location: str,
    pickup_location: str,
    dropoff_location: str,
) -> RouteResult:
    current = geocode(current_location)
    pickup = geocode(pickup_location)
    dropoff = geocode(dropoff_location)

    legs: list[RouteLeg] = []
    all_coords: list[list[float]] = []

    if not locations_match(current_location, pickup_location):
        deadhead = _route_leg(current, pickup)
        legs.append(deadhead)
        all_coords.extend(deadhead.coordinates)

    loaded = _route_leg(pickup, dropoff)
    legs.append(loaded)
    if all_coords and loaded.coordinates:
        all_coords.extend(loaded.coordinates[1:])
    else:
        all_coords.extend(loaded.coordinates)

    total_distance = sum(leg.distance_miles for leg in legs)
    total_duration = sum(leg.duration_hours for leg in legs)

    return RouteResult(
        total_distance_miles=total_distance,
        total_drive_duration_hours=total_duration,
        polyline=all_coords,
        legs=legs,
        points={"current": current, "pickup": pickup, "dropoff": dropoff},
    )


def interpolate_along_route(
    polyline: list[list[float]],
    fraction: float,
) -> tuple[float, float]:
    if not polyline:
        return 0.0, 0.0
    fraction = max(0.0, min(1.0, fraction))
    if len(polyline) == 1:
        return polyline[0][1], polyline[0][0]

    segment_lengths: list[float] = []
    total = 0.0
    for i in range(len(polyline) - 1):
        lng1, lat1 = polyline[i]
        lng2, lat2 = polyline[i + 1]
        length = haversine_miles(lat1, lng1, lat2, lng2)
        segment_lengths.append(length)
        total += length

    if total == 0:
        lng, lat = polyline[0]
        return lat, lng

    target = fraction * total
    walked = 0.0
    for i, length in enumerate(segment_lengths):
        if walked + length >= target:
            ratio = (target - walked) / length if length else 0
            lng1, lat1 = polyline[i]
            lng2, lat2 = polyline[i + 1]
            lng = lng1 + (lng2 - lng1) * ratio
            lat = lat1 + (lat2 - lat1) * ratio
            return lat, lng
        walked += length

    lng, lat = polyline[-1]
    return lat, lng


def point_at_distance_miles(
    polyline: list[list[float]],
    distance_miles: float,
    total_miles: float,
) -> tuple[float, float]:
    if total_miles <= 0:
        return interpolate_along_route(polyline, 0)
    return interpolate_along_route(polyline, distance_miles / total_miles)
