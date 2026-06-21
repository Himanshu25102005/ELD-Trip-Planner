import { GRID, ROWS } from "./LogSheetGrid";

export default function LogSheetTotals({ totals }) {
  const totalHeight = GRID.headerHeight + GRID.marginTop + ROWS.length * GRID.rowHeight + 16;

  return (
    <svg
      viewBox={`0 0 ${GRID.labelWidth + GRID.width + GRID.totalsWidth} ${totalHeight}`}
      className="pointer-events-none absolute inset-0 w-full min-w-[800px]"
      aria-hidden
    >
      {ROWS.map((row, rowIndex) => {
        const y = GRID.headerHeight + GRID.marginTop + rowIndex * GRID.rowHeight + GRID.rowHeight / 2 + 4;
        const key = `${row.key}_hours`;
        const value = totals[key] ?? 0;
        return (
          <text
            key={row.key}
            x={GRID.labelWidth + GRID.width + GRID.totalsWidth / 2}
            y={y}
            textAnchor="middle"
            fontSize="11"
            fill="#111827"
            fontWeight="600"
          >
            {value.toFixed(1)}
          </text>
        );
      })}
    </svg>
  );
}
