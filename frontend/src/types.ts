export type Status = "SAFE" | "WARNING" | "UNSAFE";

export interface Aircraft {
  id: string;
  name: string;
  max_wind_speed_mps: number;
  max_gust_speed_mps: number;
  max_precipitation_mm_per_hour: number;
  min_temperature_c: number;
  max_temperature_c: number;
  created_at: string;
}

export interface Waypoint {
  sequence: number;
  latitude: number;
  longitude: number;
}

export interface Mission {
  id: string;
  aircraft_id: string;
  name: string;
  planned_departure_at: string;
  waypoints: Waypoint[];
  created_at: string;
}

export interface Constraint {
  metric: string;
  status: Status;
  value: number | null;
  limit: number | string;
  margin: number | null;
  reason: string;
}

export interface Segment {
  segment_index: number;
  status: Status;
  constraints: Constraint[];
}

export interface Assessment {
  id: string;
  mission_id: string;
  candidate_departure_at: string;
  status: Status;
  limiting_factor: string;
  rule_version: string;
  details: {
    status: Status;
    limiting_factor: string;
    rule_version: string;
    segments: Segment[];
  };
  snapshot: {
    id: string;
    provider: string;
    retrieved_at: string;
    observations: Record<string, unknown>[];
  };
  created_at: string;
}

export interface WindowResponse {
  mission_id: string;
  interval_minutes: number;
  candidates: {
    departure_at: string;
    status: Status;
    limiting_factor: string;
  }[];
  windows: {
    start_at: string;
    end_at: string;
    best_status: Status;
  }[];
}
