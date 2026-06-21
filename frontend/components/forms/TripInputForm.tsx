"use client";

import { useState } from "react";

const defaultValues = {
  current_location: "Dallas, TX",
  pickup_location: "Dallas, TX",
  dropoff_location: "Denver, CO",
  current_cycle_used_hours: 10,
};

export default function TripInputForm({ onSubmit, loading }) {
  const [form, setForm] = useState(defaultValues);

  function handleChange(e) {
    const { name, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]:
        name === "current_cycle_used_hours" ? parseFloat(value) || 0 : value,
    }));
  }

  function handleSubmit(e) {
    e.preventDefault();
    onSubmit(form);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <Field
        label="Current location"
        name="current_location"
        value={form.current_location}
        onChange={handleChange}
        placeholder="Where is the truck now?"
      />
      <Field
        label="Pickup location"
        name="pickup_location"
        value={form.pickup_location}
        onChange={handleChange}
        placeholder="Where cargo is picked up"
      />
      <Field
        label="Dropoff location"
        name="dropoff_location"
        value={form.dropoff_location}
        onChange={handleChange}
        placeholder="Final delivery location"
      />
      <Field
        label="Cycle hours used (0–70)"
        name="current_cycle_used_hours"
        type="number"
        min={0}
        max={70}
        step={0.5}
        value={form.current_cycle_used_hours}
        onChange={handleChange}
        hint="Hours already used in your rolling 70-hour / 8-day window"
      />

      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? "Planning trip…" : "Plan Trip"}
      </button>
    </form>
  );
}

function Field({ label, hint, ...props }: { label: string; hint?: string; [key: string]: unknown }) {
  return (
    <div>
      <label className="mb-1.5 block text-sm font-medium text-slate-700">
        {label}
      </label>
      <input
        {...props}
        className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm text-slate-900 outline-none ring-blue-500 transition focus:border-blue-500 focus:ring-2"
      />
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}
