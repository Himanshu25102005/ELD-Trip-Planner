import SectionCard from "../layout/SectionCard";
import { formatHours } from "../../lib/format";
import type { ReviewerStats, TripPlanResponse } from "../../lib/types";

export default function ReviewerPanel({
  reviewer,
  plan,
}: {
  reviewer: ReviewerStats;
  plan: TripPlanResponse;
}) {
  if (!reviewer) return null;

  return (
    <SectionCard
      title="Assessment Review"
      subtitle="Raw trip metrics and hardcoded assumptions for quick reviewer verification."
    >
      <div className="grid gap-6 lg:grid-cols-2">
        <div>
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
            Trip Metrics
          </h3>
          <dl className="space-y-2 text-sm">
            <Row label="Route distance" value={`${reviewer.route_distance_miles?.toLocaleString()} mi`} />
            <Row label="Raw drive time (routing)" value={formatHours(reviewer.raw_drive_time_hours)} />
            <Row label="Total driving time (simulated)" value={formatHours(reviewer.total_driving_hours)} highlight />
            <Row label="Total on-duty time" value={formatHours(reviewer.total_on_duty_hours)} />
            <Row label="Total off-duty time" value={formatHours(reviewer.total_off_duty_hours)} />
            <Row label="Total trip duration" value={formatHours(reviewer.trip_duration_hours)} />
            <Row label="Calendar days (logs)" value={String(plan.summary?.total_days ?? "—")} />
            <Row label="Duty periods" value={String(reviewer.duty_period_count)} />
            <Row label="Fuel stops" value={String(reviewer.fuel_stop_count)} />
            <Row label="Rest stops" value={String(reviewer.rest_stop_count)} />
            <Row label="30-min breaks" value={String(reviewer.break_count)} />
            <Row label="10-hour resets" value={String(reviewer.ten_hour_reset_count)} />
            <Row label="34-hour restarts" value={String(reviewer.thirty_four_hour_restart_count)} />
            <Row label="Cycle at trip start" value={formatHours(reviewer.cycle_hours_at_start)} />
            <Row label="Cycle at trip end" value={formatHours(reviewer.cycle_hours_at_end)} />
          </dl>
        </div>

        <div>
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
            Assessment Assumptions
          </h3>
          <ul className="space-y-2">
            {reviewer.assumptions.map((item) => (
              <li
                key={item.id}
                className="flex items-start gap-2 rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 text-sm"
              >
                <span className="font-bold text-emerald-600" aria-hidden>
                  ✓
                </span>
                <span className="text-slate-800">{item.label}</span>
              </li>
            ))}
          </ul>

          <div className="mt-5 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
            <p className="font-medium text-slate-900">Duty period vs. calendar day</p>
            <p className="mt-1 leading-relaxed">
              Daily log sheets split at midnight for FMCSA display. Driving totals on a calendar
              day may exceed 11 hours when one duty period crosses midnight — limits are enforced
              per duty period in the HOS engine, not per log sheet day.
            </p>
          </div>
        </div>
      </div>
    </SectionCard>
  );
}

function Row({ label, value, highlight = false }) {
  return (
    <div className="flex justify-between gap-4 border-b border-slate-100 py-1.5 last:border-0">
      <dt className="text-slate-500">{label}</dt>
      <dd className={`font-medium ${highlight ? "text-blue-700" : "text-slate-900"}`}>{value}</dd>
    </div>
  );
}
