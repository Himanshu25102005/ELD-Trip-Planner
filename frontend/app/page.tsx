"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import Header from "../components/layout/Header";
import TripInputForm from "../components/forms/TripInputForm";
import { planTrip } from "../lib/api";

export default function HomePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(formData) {
    setLoading(true);
    setError("");
    try {
      const result = await planTrip(formData);
      sessionStorage.setItem("tripPlan", JSON.stringify(result));
      sessionStorage.setItem("tripInput", JSON.stringify(formData));
      router.push("/results");
    } catch (err) {
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto flex max-w-xl flex-col gap-8 px-4 py-12">
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            Plan Your Trip
          </h1>
          <p className="mt-2 text-slate-600">
            Enter your route and current HOS cycle usage to generate a compliant
            driving schedule and daily log sheets.
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          <TripInputForm onSubmit={handleSubmit} loading={loading} />
          {error && (
            <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}
        </div>

        <p className="text-center text-sm text-slate-500">
          Simulation uses FMCSA 70-hour/8-day rules with 11-hour driving and
          14-hour duty limits.
        </p>
      </main>
    </div>
  );
}
