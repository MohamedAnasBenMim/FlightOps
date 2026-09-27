import type { Aircraft, Assessment, Mission, WindowResponse } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

interface ApiErrorBody {
  error?: {
    message?: string;
  };
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers
    }
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ApiErrorBody;
    throw new Error(body.error?.message ?? `Request failed (${response.status})`);
  }
  return (await response.json()) as T;
}

export const api = {
  listAircraft: () => request<Aircraft[]>("/api/v1/aircraft"),
  createAircraft: (payload: Omit<Aircraft, "id" | "created_at">) =>
    request<Aircraft>("/api/v1/aircraft", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  listMissions: () => request<Mission[]>("/api/v1/missions"),
  createMission: (payload: {
    aircraft_id: string;
    name: string;
    planned_departure_at: string;
    waypoints: { latitude: number; longitude: number }[];
  }) =>
    request<Mission>("/api/v1/missions", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  assessMission: (missionId: string) =>
    request<Assessment>(`/api/v1/missions/${missionId}/assessments`, {
      method: "POST",
      body: "{}"
    }),
  getWindows: (
    missionId: string,
    startAt: string,
    endAt: string,
    intervalMinutes = 60
  ) => {
    const params = new URLSearchParams({
      start_at: startAt,
      end_at: endAt,
      interval_minutes: String(intervalMinutes)
    });
    return request<WindowResponse>(
      `/api/v1/missions/${missionId}/flight-windows?${params}`
    );
  }
};
