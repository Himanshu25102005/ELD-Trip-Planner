import SectionCard from "../layout/SectionCard";
import type { ComplianceSummary as ComplianceData } from "../../lib/types";

export default function ComplianceSummaryPanel({ compliance }: { compliance: ComplianceData }) {
  if (!compliance) return null;

  const isCompliant = compliance.compliant;

  return (
    <SectionCard accent={isCompliant}>
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            FMCSA Compliance Check
          </p>
          <p
            className={`mt-1 text-2xl font-bold tracking-tight ${
              isCompliant ? "text-emerald-700" : "text-red-700"
            }`}
          >
            {compliance.status}
          </p>
        </div>
        <div className="rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-700">
          {compliance.checks_passed} / {compliance.checks_total} rules passed
        </div>
      </div>

      <ul className="space-y-3">
        {compliance.checks.map((check) => (
          <li
            key={check.rule_id}
            className="flex gap-3 rounded-xl border border-slate-100 bg-slate-50/60 px-4 py-3"
          >
            <span
              className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                check.passed
                  ? "bg-emerald-100 text-emerald-700"
                  : "bg-red-100 text-red-700"
              }`}
              aria-hidden
            >
              {check.passed ? "✓" : "✗"}
            </span>
            <div>
              <p className="font-medium text-slate-900">{check.rule}</p>
              <p className="mt-0.5 text-sm text-slate-600">{check.detail}</p>
            </div>
          </li>
        ))}
      </ul>

      <p className="mt-5 rounded-lg border border-blue-100 bg-blue-50 px-4 py-3 text-sm leading-relaxed text-blue-900">
        {compliance.explanation}
      </p>
    </SectionCard>
  );
}
