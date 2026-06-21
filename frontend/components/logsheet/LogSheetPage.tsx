import LogSheetGrid from "./LogSheetGrid";
import LogSheetEvents, { LogSheetRemarks } from "./LogSheetEvents";
import LogSheetTotals from "./LogSheetTotals";

export default function LogSheetPage({ day_index, date, events, totals, reviewerMode = false }) {
  const formattedDate = new Date(date + "T12:00:00").toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  const calendarDrivingExceeds11 = totals.driving_hours > 11.01;

  return (
    <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 bg-slate-50 px-6 py-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h3 className="text-lg font-semibold text-slate-900">
            Day {day_index} — Driver&apos;s Daily Log
          </h3>
          <time className="text-sm text-slate-600">{formattedDate}</time>
        </div>
        <p className="mt-1 text-xs text-slate-500">
          Original — File at home terminal. Duplicate — Driver retains for 8 days.
        </p>
        {(reviewerMode || calendarDrivingExceeds11) && calendarDrivingExceeds11 && (
          <p className="mt-2 rounded-md border border-blue-100 bg-blue-50 px-3 py-2 text-xs text-blue-900">
            This calendar day shows {totals.driving_hours.toFixed(1)}h driving because a duty
            period crosses midnight. The 11-hour limit applies to the full duty period, not this
            single day.
          </p>
        )}
      </div>

      <div className="overflow-x-auto px-4 py-4">
        <div className="relative min-w-[800px]">
          <LogSheetGrid />
          <LogSheetEvents events={events} />
          <LogSheetTotals totals={totals} />
        </div>
      </div>

      <div className="border-t border-slate-200 px-6 py-4">
        <LogSheetRemarks events={events} />
        <div className="mt-4 grid grid-cols-2 gap-4 text-xs text-slate-600 sm:grid-cols-4">
          <Total label="Off duty" value={totals.off_duty_hours} />
          <Total label="Sleeper" value={totals.sleeper_berth_hours} />
          <Total label="Driving" value={totals.driving_hours} />
          <Total label="On duty" value={totals.on_duty_hours} />
        </div>
      </div>
    </article>
  );
}

function Total({ label, value }) {
  return (
    <div className="rounded-lg bg-slate-50 px-3 py-2">
      <span className="text-slate-500">{label}: </span>
      <span className="font-semibold text-slate-900">{value.toFixed(1)}h</span>
    </div>
  );
}
