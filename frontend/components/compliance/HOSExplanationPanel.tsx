"use client";

import { useState } from "react";
import SectionCard from "../layout/SectionCard";
import { formatDateTime, formatHours } from "../../lib/format";
import type { HOSExplanation } from "../../lib/types";

export default function HOSExplanationPanel({
  explanations,
}: {
  explanations: HOSExplanation[];
}) {
  const [open, setOpen] = useState(true);

  if (!explanations?.length) return null;

  return (
    <SectionCard>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between text-left"
      >
        <div>
          <h2 className="text-lg font-semibold text-slate-900">
            Why was this schedule generated?
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            Event-driven explanations from the HOS simulation ({explanations.length} events)
          </p>
        </div>
        <span className="ml-4 text-slate-400">{open ? "▾" : "▸"}</span>
      </button>

      {open && (
        <ol className="mt-5 space-y-3 border-t border-slate-100 pt-5">
          {explanations.map((item, index) => (
            <li
              key={`${item.start}-${index}`}
              className="flex gap-4 rounded-lg border border-slate-100 bg-slate-50/60 px-4 py-3"
            >
              <span className="shrink-0 text-xs font-semibold text-slate-400">
                {String(index + 1).padStart(2, "0")}
              </span>
              <div>
                <p className="text-sm font-medium text-slate-900">
                  {formatDateTime(item.start)}
                  {item.duration_hours > 0 && (
                    <span className="ml-2 font-normal text-slate-500">
                      ({formatHours(item.duration_hours)})
                    </span>
                  )}
                </p>
                <p className="mt-1 text-sm leading-relaxed text-slate-700">{item.message}</p>
                {item.location_label && (
                  <p className="mt-1 text-xs text-slate-500">{item.location_label}</p>
                )}
              </div>
            </li>
          ))}
        </ol>
      )}
    </SectionCard>
  );
}
