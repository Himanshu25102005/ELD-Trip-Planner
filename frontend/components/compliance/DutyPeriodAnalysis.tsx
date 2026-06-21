import SectionCard from "../layout/SectionCard";
import { formatDateTime, formatHours } from "../../lib/format";
import type { DutyPeriod } from "../../lib/types";

export default function DutyPeriodAnalysis({ dutyPeriods }: { dutyPeriods: DutyPeriod[] }) {
  if (!dutyPeriods?.length) return null;

  return (
    <SectionCard
      title="Duty Period Analysis"
      subtitle="FMCSA daily limits apply per duty period, not per calendar day. A period may span midnight — that is why log sheet days can show more than 11 driving hours."
    >
      <div className="space-y-4">
        {dutyPeriods.map((period) => (
          <div
            key={period.index}
            className="rounded-xl border border-slate-200 bg-slate-50/50 p-5"
          >
            <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
              <h3 className="text-base font-semibold text-slate-900">
                Duty Period {period.index}
              </h3>
              <p className="text-sm text-slate-500">
                {formatDateTime(period.start)} → {formatDateTime(period.end)}
              </p>
            </div>

            <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <Metric label="Driving Hours" value={formatHours(period.driving_hours)} highlight />
              <Metric label="On Duty Hours" value={formatHours(period.on_duty_hours)} />
              <Metric label="Off Duty (in period)" value={formatHours(period.off_duty_hours)} />
              <Metric
                label="Remaining 11-Hr Limit"
                value={formatHours(Math.max(0, period.remaining_11_hour_limit))}
                ok={period.driving_hours <= 11}
              />
              <Metric
                label="Remaining 14-Hr Window"
                value={formatHours(Math.max(0, period.remaining_14_hour_window))}
                ok={period.remaining_14_hour_window >= 0}
              />
              <Metric
                label="Max Allowed Driving"
                value={`${period.max_driving_hours}h / period`}
              />
            </dl>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}

function Metric({ label, value, highlight = false, ok = true }) {
  return (
    <div
      className={`rounded-lg border px-3 py-2.5 ${
        highlight ? "border-blue-200 bg-blue-50/50" : "border-slate-200 bg-white"
      }`}
    >
      <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</dt>
      <dd
        className={`mt-0.5 text-lg font-semibold ${
          ok ? "text-slate-900" : "text-red-700"
        }`}
      >
        {value}
      </dd>
    </div>
  );
}
