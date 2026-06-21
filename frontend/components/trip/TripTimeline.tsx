import SectionCard from "../layout/SectionCard";
import { formatDateTime, formatHours } from "../../lib/format";
import type { TimelineEvent } from "../../lib/types";

const TYPE_STYLES = {
  pickup: "border-blue-200 bg-blue-50 text-blue-800",
  dropoff: "border-red-200 bg-red-50 text-red-800",
  fuel: "border-amber-200 bg-amber-50 text-amber-900",
  break: "border-violet-200 bg-violet-50 text-violet-800",
  rest: "border-emerald-200 bg-emerald-50 text-emerald-800",
  restart: "border-emerald-200 bg-emerald-50 text-emerald-800",
  driving: "border-slate-200 bg-white text-slate-800",
  on_duty: "border-slate-200 bg-slate-50 text-slate-800",
  off_duty: "border-slate-100 bg-slate-50 text-slate-600",
};

export default function TripTimeline({ timeline }: { timeline: TimelineEvent[] }) {
  if (!timeline?.length) return null;

  const notable = timeline.filter(
    (e) =>
      e.stop_type ||
      e.status === "driving" ||
      (e.status === "on_duty" && e.duration_hours >= 0.5)
  );

  return (
    <SectionCard
      title="Trip Timeline"
      subtitle="Chronological sequence of duty status changes, stops, and driving segments."
    >
      <div className="relative space-y-0">
        <div className="absolute bottom-2 left-[11px] top-2 w-px bg-slate-200" aria-hidden />
        {notable.map((event, index) => {
          const styleKey = event.stop_type || event.status;
          const style = TYPE_STYLES[styleKey] || TYPE_STYLES.off_duty;

          return (
            <div key={`${event.start}-${index}`} className="relative flex gap-4 pb-5 last:pb-0">
              <div
                className={`relative z-10 mt-1.5 h-3 w-3 shrink-0 rounded-full border-2 border-white ring-2 ring-slate-200 ${
                  event.stop_type === "fuel"
                    ? "bg-amber-400"
                    : event.stop_type === "rest" || event.stop_type === "restart"
                      ? "bg-emerald-500"
                      : event.status === "driving"
                        ? "bg-blue-500"
                        : "bg-slate-400"
                }`}
              />
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <time className="text-sm font-semibold text-slate-900">
                    {formatDateTime(event.start)}
                  </time>
                  <span className={`rounded-full border px-2 py-0.5 text-xs font-medium ${style}`}>
                    {event.title}
                  </span>
                  {event.duration_hours > 0 && (
                    <span className="text-xs text-slate-500">
                      {formatHours(event.duration_hours)}
                    </span>
                  )}
                </div>
                {event.location_label && (
                  <p className="mt-1 text-sm text-slate-600">{event.location_label}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </SectionCard>
  );
}
