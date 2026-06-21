export type DutyStatus = "off_duty" | "sleeper_berth" | "driving" | "on_duty";

export interface LogEvent {
  status: DutyStatus;
  start: string;
  end: string;
  location_label?: string;
}

export interface LogDay {
  day_index: number;
  date: string;
  events: LogEvent[];
  totals: {
    off_duty_hours: number;
    sleeper_berth_hours: number;
    driving_hours: number;
    on_duty_hours: number;
  };
}

export interface RouteStop {
  type: "pickup" | "dropoff" | "fuel" | "rest";
  label: string;
  lat: number;
  lng: number;
  arrival_time: string;
  departure_time: string;
}

export interface ComplianceCheck {
  rule: string;
  rule_id: string;
  passed: boolean;
  detail: string;
}

export interface ComplianceSummary {
  compliant: boolean;
  status: string;
  checks_passed: number;
  checks_total: number;
  checks: ComplianceCheck[];
  explanation: string;
}

export interface DutyPeriod {
  index: number;
  start: string;
  end: string;
  driving_hours: number;
  on_duty_hours: number;
  off_duty_hours: number;
  remaining_11_hour_limit: number;
  remaining_14_hour_window: number;
  max_driving_hours: number;
  max_duty_window_hours: number;
}

export interface TimelineEvent {
  status: DutyStatus;
  stop_type: string | null;
  start: string;
  end: string;
  duration_hours: number;
  location_label: string;
  lat?: number;
  lng?: number;
  title: string;
}

export interface HOSExplanation {
  code: string;
  start: string;
  end: string;
  duration_hours: number;
  location_label: string;
  message: string;
}

export interface FuelStopDetail {
  index: number;
  type: "fuel";
  label: string;
  mile_marker: number | null;
  arrival_time: string;
  departure_time: string;
  duration_hours: number;
  duration_minutes: number;
  reason: string;
  lat?: number;
  lng?: number;
}

export interface RestStopDetail {
  index: number;
  type: "rest" | "restart";
  label: string;
  mile_marker: number | null;
  arrival_time: string;
  departure_time: string;
  duration_hours: number;
  hos_rule_triggered: string;
  reason: string;
  lat?: number;
  lng?: number;
}

export interface StopDetails {
  fuel_stops: FuelStopDetail[];
  rest_stops: RestStopDetail[];
}

export interface ReviewerAssumption {
  id: string;
  label: string;
  applied: boolean;
}

export interface ReviewerStats {
  route_distance_miles: number;
  raw_drive_time_hours: number;
  total_driving_hours: number;
  total_on_duty_hours: number;
  total_off_duty_hours: number;
  trip_duration_hours: number;
  fuel_stop_count: number;
  rest_stop_count: number;
  break_count: number;
  duty_period_count: number;
  ten_hour_reset_count: number;
  thirty_four_hour_restart_count: number;
  cycle_hours_at_start: number;
  cycle_hours_at_end: number;
  requires_restart_at_trip_start: boolean;
  assumptions: ReviewerAssumption[];
}

export interface TripPlanInput {
  current_location: string;
  pickup_location: string;
  dropoff_location: string;
  current_cycle_used_hours: number;
}

export interface TripPlanResponse {
  requires_restart?: boolean;
  route: {
    total_distance_miles: number;
    total_drive_duration_hours: number;
    polyline: number[][];
    stops: RouteStop[];
  };
  summary: {
    total_days: number;
    total_fuel_stops: number;
    total_rest_stops: number;
    trip_start: string;
    trip_end: string;
  };
  logs: LogDay[];
  compliance?: ComplianceSummary;
  duty_periods?: DutyPeriod[];
  timeline?: TimelineEvent[];
  hos_explanations?: HOSExplanation[];
  stop_details?: StopDetails;
  reviewer?: ReviewerStats;
}

export interface ApiError {
  errors?: Record<string, string[] | string>;
  error?: string;
}
