const ROWS = [
  { key: "off_duty", label: "Off Duty" },
  { key: "sleeper_berth", label: "Sleeper Berth" },
  { key: "driving", label: "Driving" },
  { key: "on_duty", label: "On Duty (not driving)" },
];

export const GRID = {
  width: 720,
  rowHeight: 36,
  labelWidth: 120,
  totalsWidth: 64,
  headerHeight: 28,
  marginTop: 8,
};

export function gridContentWidth() {
  return GRID.width;
}

export function rowY(status) {
  const index = ROWS.findIndex((r) => r.key === status);
  const i = index >= 0 ? index : 0;
  return GRID.headerHeight + GRID.marginTop + i * GRID.rowHeight + GRID.rowHeight / 2;
}

export function timeToX(hhmm, gridWidth = GRID.width) {
  const [h, m] = hhmm.split(":").map(Number);
  let hours = h + m / 60;
  if (hhmm === "24:00") hours = 24;
  if (hours >= 23.99 && hhmm.startsWith("23:59")) hours = 24;
  return (hours / 24) * gridWidth;
}

export default function LogSheetGrid() {
  const totalHeight = GRID.headerHeight + GRID.marginTop + ROWS.length * GRID.rowHeight + 16;

  return (
    <svg
      viewBox={`0 0 ${GRID.labelWidth + GRID.width + GRID.totalsWidth} ${totalHeight}`}
      className="w-full min-w-[800px]"
      role="img"
      aria-label="24-hour duty status grid"
    >
      {/* Hour header bar */}
      <rect
        x={GRID.labelWidth}
        y={0}
        width={GRID.width}
        height={GRID.headerHeight}
        fill="#111827"
      />
      {[0, 6, 12, 18, 24].map((hour) => {
        const label = hour === 0 || hour === 24 ? "Midnight" : hour === 12 ? "Noon" : `${hour}`;
        const x = GRID.labelWidth + (hour / 24) * GRID.width;
        return (
          <text
            key={hour}
            x={x}
            y={GRID.headerHeight - 8}
            textAnchor="middle"
            fill="white"
            fontSize="9"
          >
            {label}
          </text>
        );
      })}

      {ROWS.map((row, rowIndex) => {
        const y = GRID.headerHeight + GRID.marginTop + rowIndex * GRID.rowHeight;
        return (
          <g key={row.key}>
            <text
              x={GRID.labelWidth - 8}
              y={y + GRID.rowHeight / 2 + 4}
              textAnchor="end"
              fontSize="10"
              fill="#334155"
            >
              {row.label}
            </text>
            <rect
              x={GRID.labelWidth}
              y={y}
              width={GRID.width}
              height={GRID.rowHeight}
              fill={rowIndex % 2 === 0 ? "#f8fafc" : "#ffffff"}
              stroke="#cbd5e1"
              strokeWidth="0.5"
            />
            {Array.from({ length: 25 }).map((_, hour) => {
              const x = GRID.labelWidth + (hour / 24) * GRID.width;
              return (
                <line
                  key={hour}
                  x1={x}
                  y1={y}
                  x2={x}
                  y2={y + GRID.rowHeight}
                  stroke={hour % 6 === 0 ? "#94a3b8" : "#e2e8f0"}
                  strokeWidth={hour % 6 === 0 ? 1 : 0.5}
                />
              );
            })}
            {[1, 2, 3].map((quarter) => {
              const x =
                GRID.labelWidth +
                ((rowIndex * 0 + quarter) / 24) * GRID.width;
              return null;
            })}
          </g>
        );
      })}

      {/* 15-minute ticks within each hour */}
      {Array.from({ length: 24 * 4 }).map((_, tick) => {
        if (tick % 4 === 0) return null;
        const x = GRID.labelWidth + (tick / (24 * 4)) * GRID.width;
        const y1 = GRID.headerHeight + GRID.marginTop;
        const y2 = y1 + ROWS.length * GRID.rowHeight;
        return (
          <line
            key={tick}
            x1={x}
            y1={y1}
            x2={x}
            y2={y2}
            stroke="#e2e8f0"
            strokeWidth="0.5"
          />
        );
      })}

      <text
        x={GRID.labelWidth + GRID.width + GRID.totalsWidth / 2}
        y={GRID.headerHeight - 8}
        textAnchor="middle"
        fontSize="8"
        fill="#64748b"
      >
        Total
      </text>
      <text
        x={GRID.labelWidth + GRID.width + GRID.totalsWidth / 2}
        y={GRID.headerHeight + GRID.marginTop + 8}
        textAnchor="middle"
        fontSize="8"
        fill="#64748b"
      >
        Hours
      </text>
    </svg>
  );
}

export { ROWS };
