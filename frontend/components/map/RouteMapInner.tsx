"use client";

import { MapContainer, TileLayer, Polyline, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import StopMarker from "./StopMarker";

const STOP_COLORS = {
  pickup: "#2563eb",
  dropoff: "#dc2626",
  fuel: "#f59e0b",
  rest: "#059669",
};

export default function RouteMapInner({ polyline, stops }) {
  const latLngs = (polyline || []).map(([lng, lat]) => [lat, lng]);

  const center =
    latLngs.length > 0
      ? [
          latLngs.reduce((s, p) => s + p[0], 0) / latLngs.length,
          latLngs.reduce((s, p) => s + p[1], 0) / latLngs.length,
        ]
      : [39.8283, -98.5795];

  // @ts-ignore react-leaflet types vary by version
  return (
    <MapContainer
      center={center}
      zoom={5}
      style={{ height: 420, width: "100%" }}
      scrollWheelZoom
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {latLngs.length > 1 && (
        <Polyline positions={latLngs} pathOptions={{ color: "#2563eb", weight: 4 }} />
      )}
      {(stops || []).map((stop, index) => (
        <StopMarker key={`${stop.type}-${index}`} stop={stop} color={STOP_COLORS[stop.type]} />
      ))}
    </MapContainer>
  );
}
