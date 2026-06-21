"use client";

import { useState } from "react";
import SectionCard from "../layout/SectionCard";
import { formatDateTime, formatHours } from "../../lib/format";
import type { StopDetails } from "../../lib/types";

export default function StopDetailsPanel({ stopDetails }: { stopDetails: StopDetails }) {
  if (!stopDetails) return null;

  const { fuel_stops = [], rest_stops = [] } = stopDetails;
  if (!fuel_stops.length && !rest_stops.length) {
    return (
      <SectionCard title="Stop Details" subtitle="No fuel or rest stops required for this trip.">
        <p className="text-sm text-slate-600">
          Route distance is under 1,000 miles and the trip fits within a single duty period
          without mandatory extended rest.
        </p>
      </SectionCard>
    );
  }

  return (
    <SectionCard
      title="Stop Details"
      subtitle="Every fuel and rest stop with the HOS rule or assessment assumption that triggered it."
    >
      <div className="space-y-6">
        {fuel_stops.length > 0 && (
          <StopGroup title={`Fuel Stops (${fuel_stops.length})`}>
            {fuel_stops.map((stop) => (
              <ExpandableStopCard
                key={`fuel-${stop.index}`}
                title={`Fuel Stop #${stop.index}`}
                accent="amber"
              >
                <DetailRow label="Mile marker" value={stop.mile_marker ? `Mile ${stop.mile_marker}` : "—"} />
                <DetailRow label="Arrival" value={formatDateTime(stop.arrival_time)} />
                <DetailRow label="Departure" value={formatDateTime(stop.departure_time)} />
                <DetailRow label="Duration" value={`${stop.duration_minutes} min (${formatHours(stop.duration_hours)})`} />
                <DetailRow label="Reason" value={stop.reason} />
                <DetailRow label="Location" value={stop.label} />
              </ExpandableStopCard>
            ))}
          </StopGroup>
        )}

        {rest_stops.length > 0 && (
          <StopGroup title={`Rest Stops (${rest_stops.length})`}>
            {rest_stops.map((stop) => (
              <ExpandableStopCard
                key={`rest-${stop.index}`}
                title={`Rest Stop #${stop.index}${stop.type === "restart" ? " (34-hr restart)" : ""}`}
                accent="emerald"
              >
                <DetailRow label="Mile marker" value={stop.mile_marker ? `Mile ${stop.mile_marker}` : "—"} />
                <DetailRow label="Arrival" value={formatDateTime(stop.arrival_time)} />
                <DetailRow label="Departure" value={formatDateTime(stop.departure_time)} />
                <DetailRow label="Duration" value={formatHours(stop.duration_hours)} />
                <DetailRow label="HOS rule triggered" value={stop.hos_rule_triggered} />
                <DetailRow label="Reason" value={stop.reason} />
                <DetailRow label="Location" value={stop.label} />
              </ExpandableStopCard>
            ))}
          </StopGroup>
        )}
      </div>
    </SectionCard>
  );
}

function StopGroup({ title, children }) {
  return (
    <div>
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">{title}</h3>
      <div className="space-y-3">{children}</div>
    </div>
  );
}

function ExpandableStopCard({ title, accent, children }) {
  const [open, setOpen] = useState(true);
  const border =
    accent === "amber" ? "border-amber-200 hover:border-amber-300" : "border-emerald-200 hover:border-emerald-300";

  return (
    <div className={`rounded-xl border bg-white ${border}`}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
      >
        <span className="font-medium text-slate-900">{title}</span>
        <span className="text-slate-400">{open ? "▾" : "▸"}</span>
      </button>
      {open && <dl className="space-y-2 border-t border-slate-100 px-4 py-3">{children}</dl>}
    </div>
  );
}

function DetailRow({ label, value }) {
  return (
    <div className="grid gap-0.5 sm:grid-cols-3 sm:gap-4">
      <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="text-sm text-slate-800 sm:col-span-2">{value}</dd>
    </div>
  );
}
