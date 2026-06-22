import type { ApiError, TripPlanInput, TripPlanResponse } from "./types";

function getApiBase(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");
  if (configured) {
    return configured;
  }
  if (process.env.NODE_ENV === "development") {
    return "http://localhost:8000";
  }
  return "";
}

export async function planTrip(input: TripPlanInput): Promise<TripPlanResponse> {
  const apiBase = getApiBase();
  if (!apiBase) {
    throw new Error(
      "NEXT_PUBLIC_API_URL is not configured. Set it in Vercel environment variables."
    );
  }

  const response = await fetch(`${apiBase}/api/plan-trip/`, {
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
