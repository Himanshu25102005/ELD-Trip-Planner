"use client";

import { Marker, Popup } from "react-leaflet";
import L from "leaflet";

function makeIcon(color) {
  return L.divIcon({
    className: "",
    html: `<div style="background:${color};width:14px;height:14px;border-radius:50%;border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,.35)"></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });
}

export default function StopMarker({ stop, color }) {
  const arrival = new Date(stop.arrival_time).toLocaleString();
  const departure = new Date(stop.departure_time).toLocaleString();

  return (
    <Marker position={[stop.lat, stop.lng]} icon={makeIcon(color)}>
      <Popup>
        <div className="text-sm">
          <p className="font-semibold capitalize">{stop.type}</p>
          <p>{stop.label}</p>
          <p className="mt-1 text-xs text-slate-600">Arrive: {arrival}</p>
          <p className="text-xs text-slate-600">Depart: {departure}</p>
        </div>
      </Popup>
    </Marker>
  );
}
