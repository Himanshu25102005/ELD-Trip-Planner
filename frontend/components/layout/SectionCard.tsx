export default function SectionCard({ title, subtitle, children, className = "", accent = false }) {
  return (
    <section
      className={`rounded-2xl border bg-white shadow-sm ${
        accent ? "border-emerald-200 ring-1 ring-emerald-100" : "border-slate-200"
      } ${className}`}
    >
      {(title || subtitle) && (
        <div className={`border-b px-6 py-4 ${accent ? "border-emerald-100 bg-emerald-50/50" : "border-slate-100 bg-slate-50/80"}`}>
          {title && <h2 className="text-lg font-semibold text-slate-900">{title}</h2>}
          {subtitle && <p className="mt-1 text-sm text-slate-600">{subtitle}</p>}
        </div>
      )}
      <div className="p-6">{children}</div>
    </section>
  );
}
