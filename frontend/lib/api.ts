import type { ApiError, TripPlanInput, TripPlanResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function planTrip(input: TripPlanInput): Promise<TripPlanResponse> {
  const response = await fetch(`${API_BASE}/api/plan-trip/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });

  const data = await response.json();

  if (!response.ok) {
    const err = data as ApiError;
    if (err.errors) {
      const messages = Object.entries(err.errors)
        .map(([field, value]) => {
          const text = Array.isArray(value) ? value.join(", ") : value;
          return `${field}: ${text}`;
        })
        .join("; ");
      throw new Error(messages || "Invalid request");
    }
    throw new Error(err.error || "Failed to plan trip");
  }

  return data as TripPlanResponse;
}
