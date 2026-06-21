import { GRID, rowY, timeToX } from "./LogSheetGrid";

export default function LogSheetEvents({ events }) {
  const paths = [];
  const remarks = [];

  let prev = null;
  for (const event of events) {
    const x1 = GRID.labelWidth + timeToX(event.start);
    const x2 = GRID.labelWidth + timeToX(event.end === "23:59" ? "24:00" : event.end);
    const y = rowY(event.status);

    paths.push(
      <line
        key={`${event.start}-${event.end}-${event.status}-h`}
        x1={x1}
        y1={y}
        x2={x2}
        y2={y}
        stroke="#111827"
        strokeWidth="2"
      />
    );

    if (prev && prev.end === event.start && prev.status !== event.status) {
      const px = GRID.labelWidth + timeToX(event.start);
      paths.push(
        <line
          key={`${event.start}-v`}
          x1={px}
          y1={rowY(prev.status)}
          x2={px}
          y2={y}
          stroke="#111827"
          strokeWidth="2"
        />
      );
    }

    if (event.location_label) {
      remarks.push({ x: x1, label: event.location_label });
    }

    prev = event;
  }

  const totalHeight = GRID.headerHeight + GRID.marginTop + 4 * GRID.rowHeight + 16;

  return (
    <svg
      viewBox={`0 0 ${GRID.labelWidth + GRID.width + GRID.totalsWidth} ${totalHeight}`}
      className="pointer-events-none absolute inset-0 w-full min-w-[800px]"
      aria-hidden
    >
      {paths}
    </svg>
  );
}

export function LogSheetRemarks({ events }) {
  const remarks = events.filter((e) => e.location_label);
  if (!remarks.length) return null;

  return (
    <div className="mt-3 border-t border-slate-200 pt-3">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
        Remarks
      </p>
      <ul className="space-y-1 text-xs text-slate-700">
        {remarks.map((event, i) => (
          <li key={i}>
            <span className="font-medium">{event.start}</span> — {event.location_label}
          </li>
        ))}
      </ul>
    </div>
  );
}
