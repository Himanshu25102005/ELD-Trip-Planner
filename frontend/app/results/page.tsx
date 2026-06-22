"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Header from "../../components/layout/Header";
import RouteMap from "../../components/map/RouteMap";
import LogSheetPage from "../../components/logsheet/LogSheetPage";
import LoadingState from "../../components/layout/LoadingState";
import ComplianceSummaryPanel from "../../components/compliance/ComplianceSummaryPanel";
import DutyPeriodAnalysis from "../../components/compliance/DutyPeriodAnalysis";
import HOSExplanationPanel from "../../components/compliance/HOSExplanationPanel";
import TripTimeline from "../../components/trip/TripTimeline";
import StopDetailsPanel from "../../components/trip/StopDetailsPanel";
import ReviewerPanel from "../../components/reviewer/ReviewerPanel";
import SectionCard from "../../components/layout/SectionCard";
import { formatHours } from "../../lib/format";

export default function ResultsPage() {
  const [plan, setPlan] = useState(null);
  const [input, setInput] = useState(null);
  const [loaded, setLoaded] = useState(false);
  const [reviewerMode, setReviewerMode] = useState(false);

  useEffect(() => {
    const stored = sessionStorage.getItem("tripPlan");
    const storedInput = sessionStorage.getItem("tripInput");
    if (stored) setPlan(JSON.parse(stored));
    if (storedInput) setInput(JSON.parse(storedInput));
    setLoaded(true);
  }, []);

  if (!loaded) {
    return (
      <div className="min-h-screen">
        <Header />
        <LoadingState message="Loading trip plan…" />
      </div>
    );
  }

  if (!plan) {
    return (
      <div className="min-h-screen">
        <Header />
        <div className="mx-auto max-w-lg px-4 py-16 text-center">
          <p className="text-slate-600">No trip plan found.</p>
          <Link href="/" className="mt-4 inline-block text-blue-600 hover:underline">
            ← Back to trip form
          </Link>
        </div>
      </div>
    );
  }

  const {
    route,
    summary,
    logs,
    requires_restart,
    compliance,
    duty_periods,
    timeline,
    hos_explanations,
    stop_details,
    reviewer,
  } = plan;

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />
      <main className="mx-auto max-w-6xl space-y-8 px-4 py-8">
        {/* Header */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">Trip Results</h1>
            {input && (
              <p className="mt-1 text-sm text-slate-600">
                {input.current_location} → {input.pickup_location} → {input.dropoff_location}
                {input.current_cycle_used_hours != null && (
                  <span className="text-slate-400"> · {input.current_cycle_used_hours}h cycle used</span>
                )}
              </p>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm">
              <input
                type="checkbox"
                checked={reviewerMode}
                onChange={(e) => setReviewerMode(e.target.checked)}
                className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="font-medium text-slate-700">Assessment Review</span>
            </label>
            <Link
              href="/"
              className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              ← Edit trip
            </Link>
          </div>
        </div>

        {requires_restart && (
          <div className="rounded-xl border border-amber-200 bg-amber-50 px-5 py-4 text-amber-900">
            <strong>34-hour restart required.</strong> Your 70-hour cycle is exhausted. The plan
            shows mandatory rest before driving can resume.
          </div>
        )}

        {/* Compliance — highest visibility */}
        {compliance && <ComplianceSummaryPanel compliance={compliance} />}

        {/* Reviewer mode panel */}
        {reviewerMode && reviewer && <ReviewerPanel reviewer={reviewer} plan={plan} />}

        {/* Route overview */}
        <div className="grid gap-6 lg:grid-cols-3">
          <SectionCard
            title="Route Summary"
            subtitle=""
            className="lg:col-span-1"
          >
            <dl className="space-y-3 text-sm">
              <SummaryRow label="Distance" value={`${route.total_distance_miles.toLocaleString()} mi`} />
              <SummaryRow label="Raw drive time" value={formatHours(route.total_drive_duration_hours)} />
              <SummaryRow label="Calendar days" value={String(summary.total_days)} />
              <SummaryRow label="Trip start" value={new Date(summary.trip_start).toLocaleString()} />
              <SummaryRow label="Trip end" value={new Date(summary.trip_end).toLocaleString()} />
              <SummaryRow label="Fuel stops" value={String(summary.total_fuel_stops)} />
              <SummaryRow label="Rest stops" value={String(summary.total_rest_stops)} />
            </dl>
          </SectionCard>

          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm lg:col-span-2">
            <RouteMap polyline={route.polyline} stops={route.stops} />
          </div>
        </div>

        {/* Explainability sections */}
        <div className="grid gap-6 lg:grid-cols-2">
          <TripTimeline timeline={timeline} />
          <StopDetailsPanel stopDetails={stop_details} />
        </div>

        {hos_explanations && <HOSExplanationPanel explanations={hos_explanations} />}

        {duty_periods && <DutyPeriodAnalysis dutyPeriods={duty_periods} />}

        {/* Daily logs */}
        <section className="space-y-4">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">Daily Log Sheets</h2>
            <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-600">
              One FMCSA-style grid per calendar day. Events crossing midnight are split across
              days for display.{" "}
              <strong className="font-medium text-slate-800">
                Calendar-day driving totals may exceed 11 hours
              </strong>{" "}
              when a single duty period spans two days — see Duty Period Analysis above for
              per-period limits.
            </p>
          </div>
          <div className="space-y-8">
            {logs.map((day) => (
              <LogSheetPage key={day.day_index} {...day} reviewerMode={reviewerMode} />
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}

function SummaryRow({ label, value }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-slate-500">{label}</dt>
      <dd className="font-medium text-slate-900">{value}</dd>
    </div>
  );
}
