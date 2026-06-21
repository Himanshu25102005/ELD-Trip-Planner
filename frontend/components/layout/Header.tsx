import Link from "next/link";

export default function Header() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
        <Link href="/" className="flex items-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600 text-sm font-bold text-white">
            ELD
          </span>
          <span className="font-semibold text-slate-900">Trip Planner</span>
        </Link>
        <span className="hidden text-sm text-slate-500 sm:inline">
          FMCSA HOS Simulation
        </span>
      </div>
    </header>
  );
}
