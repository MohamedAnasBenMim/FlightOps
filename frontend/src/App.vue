<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { api } from "./api";
import type { Aircraft, Assessment, Mission, Status, WindowResponse } from "./types";

const aircraft = ref<Aircraft[]>([]);
const missions = ref<Mission[]>([]);
const selectedMissionId = ref("");
const assessment = ref<Assessment | null>(null);
const windows = ref<WindowResponse | null>(null);
const error = ref("");
const notice = ref("");
const pending = ref("");

const aircraftForm = ref({
  name: "",
  max_wind_speed_mps: 12,
  max_gust_speed_mps: 18,
  max_precipitation_mm_per_hour: 2,
  min_temperature_c: -10,
  max_temperature_c: 45
});

const missionForm = ref({
  aircraft_id: "",
  name: "",
  planned_departure_at: localDateTime(new Date(Date.now() + 60 * 60 * 1000)),
  waypoints: [
    { latitude: 36.8065, longitude: 10.1815 },
    { latitude: 36.85, longitude: 10.25 }
  ]
});

const windowForm = ref({
  start_at: localDateTime(new Date(Date.now() + 60 * 60 * 1000)),
  end_at: localDateTime(new Date(Date.now() + 7 * 60 * 60 * 1000)),
  interval_minutes: 60
});

const selectedMission = computed(
  () => missions.value.find((mission) => mission.id === selectedMissionId.value) ?? null
);

function localDateTime(date: Date): string {
  const shifted = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return shifted.toISOString().slice(0, 16);
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function statusClass(status: Status): string {
  return `status status--${status.toLowerCase()}`;
}

async function perform(label: string, operation: () => Promise<void>): Promise<void> {
  pending.value = label;
  error.value = "";
  notice.value = "";
  try {
    await operation();
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : "An unexpected error occurred";
  } finally {
    pending.value = "";
  }
}

async function refresh(): Promise<void> {
  const [aircraftData, missionData] = await Promise.all([
    api.listAircraft(),
    api.listMissions()
  ]);
  aircraft.value = aircraftData;
  missions.value = missionData;
  if (!missionForm.value.aircraft_id && aircraftData[0]) {
    missionForm.value.aircraft_id = aircraftData[0].id;
  }
  if (!selectedMissionId.value && missionData[0]) {
    selectedMissionId.value = missionData[0].id;
  }
}

async function submitAircraft(): Promise<void> {
  await perform("aircraft", async () => {
    const created = await api.createAircraft(aircraftForm.value);
    aircraft.value.unshift(created);
    missionForm.value.aircraft_id = created.id;
    aircraftForm.value.name = "";
    notice.value = "Aircraft saved. It is ready to use in a mission.";
  });
}

async function submitMission(): Promise<void> {
  await perform("mission", async () => {
    const created = await api.createMission({
      ...missionForm.value,
      planned_departure_at: new Date(missionForm.value.planned_departure_at).toISOString()
    });
    missions.value.unshift(created);
    selectedMissionId.value = created.id;
    assessment.value = null;
    windows.value = null;
    missionForm.value.name = "";
    notice.value = "Mission saved with its ordered route.";
  });
}

async function runAssessment(): Promise<void> {
  if (!selectedMissionId.value) return;
  await perform("assessment", async () => {
    assessment.value = await api.assessMission(selectedMissionId.value);
    notice.value = "Assessment stored with an immutable weather snapshot.";
  });
}

async function findWindows(): Promise<void> {
  if (!selectedMissionId.value) return;
  await perform("windows", async () => {
    windows.value = await api.getWindows(
      selectedMissionId.value,
      new Date(windowForm.value.start_at).toISOString(),
      new Date(windowForm.value.end_at).toISOString(),
      windowForm.value.interval_minutes
    );
    notice.value = "Candidate departures evaluated.";
  });
}

function addWaypoint(): void {
  const previous = missionForm.value.waypoints.at(-1) ?? {
    latitude: 36.8065,
    longitude: 10.1815
  };
  missionForm.value.waypoints.push({
    latitude: previous.latitude,
    longitude: previous.longitude
  });
}

function removeWaypoint(index: number): void {
  if (missionForm.value.waypoints.length > 2) {
    missionForm.value.waypoints.splice(index, 1);
  }
}

onMounted(() => perform("startup", refresh));
</script>

<template>
  <div class="shell">
    <header class="topbar">
      <a class="brand" href="#" aria-label="FlightOps home">
        <span class="brand__mark">FO</span>
        <span>
          <strong>FlightOps</strong>
          <small>Mission decision support</small>
        </span>
      </a>
      <div class="system-state">
        <span class="pulse"></span>
        Local operations console
      </div>
    </header>

    <main>
      <section class="hero">
        <div>
          <p class="eyebrow">Weather-aware operations</p>
          <h1>Plan with evidence.<br /><em>Fly with context.</em></h1>
          <p class="hero__copy">
            Compare route-level forecasts with aircraft limits, preserve every
            input, and understand the constraint behind each result.
          </p>
        </div>
        <aside class="safety-note">
          <span>Decision-support prototype</span>
          <p>
            FlightOps is not a certified aviation safety system and must not be
            the sole basis for a real-world flight decision.
          </p>
        </aside>
      </section>

      <div v-if="error" class="message message--error" role="alert">{{ error }}</div>
      <div v-if="notice" class="message message--success" role="status">{{ notice }}</div>

      <section class="workspace">
        <article class="panel">
          <div class="panel__heading">
            <span class="step">01</span>
            <div>
              <h2>Aircraft envelope</h2>
              <p>Register the limits used by the deterministic rule engine.</p>
            </div>
          </div>

          <form class="form-grid" @submit.prevent="submitAircraft">
            <label class="field field--wide">
              <span>Aircraft name</span>
              <input v-model.trim="aircraftForm.name" required maxlength="120" placeholder="Surveyor X1" />
            </label>
            <label class="field">
              <span>Max wind <b>m/s</b></span>
              <input v-model.number="aircraftForm.max_wind_speed_mps" type="number" min="0" step="0.1" required />
            </label>
            <label class="field">
              <span>Max gust <b>m/s</b></span>
              <input v-model.number="aircraftForm.max_gust_speed_mps" type="number" min="0" step="0.1" required />
            </label>
            <label class="field">
              <span>Max rain <b>mm/h</b></span>
              <input v-model.number="aircraftForm.max_precipitation_mm_per_hour" type="number" min="0" step="0.1" required />
            </label>
            <label class="field">
              <span>Min temp <b>°C</b></span>
              <input v-model.number="aircraftForm.min_temperature_c" type="number" step="0.1" required />
            </label>
            <label class="field">
              <span>Max temp <b>°C</b></span>
              <input v-model.number="aircraftForm.max_temperature_c" type="number" step="0.1" required />
            </label>
            <button class="button button--dark field--wide" :disabled="!!pending">
              {{ pending === "aircraft" ? "Saving…" : "Save aircraft" }}
            </button>
          </form>

          <div v-if="aircraft.length" class="inventory">
            <p class="label">Fleet · {{ aircraft.length }}</p>
            <div v-for="item in aircraft" :key="item.id" class="inventory__row">
              <strong>{{ item.name }}</strong>
              <span>{{ item.max_wind_speed_mps }} m/s wind</span>
              <span>{{ item.min_temperature_c }}–{{ item.max_temperature_c }} °C</span>
            </div>
          </div>
        </article>

        <article class="panel">
          <div class="panel__heading">
            <span class="step">02</span>
            <div>
              <h2>Mission route</h2>
              <p>Build an ordered WGS84 route with a timezone-aware departure.</p>
            </div>
          </div>

          <form class="form-grid" @submit.prevent="submitMission">
            <label class="field">
              <span>Aircraft</span>
              <select v-model="missionForm.aircraft_id" required>
                <option value="" disabled>Select aircraft</option>
                <option v-for="item in aircraft" :key="item.id" :value="item.id">
                  {{ item.name }}
                </option>
              </select>
            </label>
            <label class="field">
              <span>Mission name</span>
              <input v-model.trim="missionForm.name" required maxlength="160" placeholder="Coastal inspection" />
            </label>
            <label class="field field--wide">
              <span>Planned departure</span>
              <input v-model="missionForm.planned_departure_at" type="datetime-local" required />
            </label>

            <div class="field field--wide">
              <div class="route-label">
                <span>Route waypoints</span>
                <button class="text-button" type="button" @click="addWaypoint">+ Add point</button>
              </div>
              <div class="waypoints">
                <div v-for="(point, index) in missionForm.waypoints" :key="index" class="waypoint">
                  <span class="waypoint__index">{{ String(index + 1).padStart(2, "0") }}</span>
                  <label>
                    <span>Latitude</span>
                    <input v-model.number="point.latitude" type="number" min="-90" max="90" step="0.000001" required />
                  </label>
                  <label>
                    <span>Longitude</span>
                    <input v-model.number="point.longitude" type="number" min="-180" max="180" step="0.000001" required />
                  </label>
                  <button
                    class="remove"
                    type="button"
                    :disabled="missionForm.waypoints.length <= 2"
                    :aria-label="`Remove waypoint ${index + 1}`"
                    @click="removeWaypoint(index)"
                  >×</button>
                </div>
              </div>
            </div>

            <button class="button button--accent field--wide" :disabled="!!pending || !aircraft.length">
              {{ pending === "mission" ? "Saving…" : "Create mission" }}
            </button>
          </form>
        </article>
      </section>

      <section class="analysis">
        <div class="analysis__header">
          <div>
            <p class="eyebrow">Operational analysis</p>
            <h2>Assess a mission</h2>
          </div>
          <select v-model="selectedMissionId" aria-label="Mission to assess">
            <option value="" disabled>Select mission</option>
            <option v-for="mission in missions" :key="mission.id" :value="mission.id">
              {{ mission.name }} · {{ formatDate(mission.planned_departure_at) }}
            </option>
          </select>
          <button class="button button--light" :disabled="!selectedMissionId || !!pending" @click="runAssessment">
            {{ pending === "assessment" ? "Assessing…" : "Run assessment" }}
          </button>
        </div>

        <div v-if="assessment" class="result-grid">
          <div class="result-summary">
            <p class="label">Mission outcome</p>
            <span :class="statusClass(assessment.status)">{{ assessment.status }}</span>
            <h3>{{ selectedMission?.name }}</h3>
            <dl>
              <div><dt>Limiting factor</dt><dd>{{ assessment.limiting_factor.replaceAll("_", " ") }}</dd></div>
              <div><dt>Rule version</dt><dd>{{ assessment.rule_version }}</dd></div>
              <div><dt>Forecast points</dt><dd>{{ assessment.snapshot.observations.length }}</dd></div>
              <div><dt>Provider</dt><dd>Open-Meteo</dd></div>
            </dl>
          </div>

          <div class="segments">
            <article v-for="segment in assessment.details.segments" :key="segment.segment_index" class="segment">
              <header>
                <div>
                  <span>Route leg {{ segment.segment_index + 1 }}</span>
                  <small>Waypoint {{ segment.segment_index + 1 }} → {{ segment.segment_index + 2 }}</small>
                </div>
                <span :class="statusClass(segment.status)">{{ segment.status }}</span>
              </header>
              <div v-for="constraint in segment.constraints" :key="constraint.metric" class="constraint">
                <div>
                  <strong>{{ constraint.metric.replaceAll("_", " ") }}</strong>
                  <small>{{ constraint.reason }}</small>
                </div>
                <div class="constraint__value">
                  {{ constraint.value ?? "Missing" }}
                  <span>/ {{ constraint.limit }}</span>
                </div>
              </div>
            </article>
          </div>
        </div>
        <div v-else class="empty-state">
          <span>↗</span>
          <p>Select a saved mission and run an assessment to inspect route-level evidence.</p>
        </div>
      </section>

      <section class="windows panel">
        <div class="panel__heading">
          <span class="step">03</span>
          <div>
            <h2>Find a better departure</h2>
            <p>Evaluate bounded candidates and group adjacent suitable times.</p>
          </div>
        </div>
        <form class="window-form" @submit.prevent="findWindows">
          <label class="field"><span>From</span><input v-model="windowForm.start_at" type="datetime-local" required /></label>
          <label class="field"><span>Until</span><input v-model="windowForm.end_at" type="datetime-local" required /></label>
          <label class="field"><span>Interval</span>
            <select v-model.number="windowForm.interval_minutes">
              <option :value="30">30 minutes</option>
              <option :value="60">1 hour</option>
              <option :value="120">2 hours</option>
            </select>
          </label>
          <button class="button button--dark" :disabled="!selectedMissionId || !!pending">
            {{ pending === "windows" ? "Evaluating…" : "Find windows" }}
          </button>
        </form>

        <div v-if="windows" class="window-results">
          <article v-for="window in windows.windows" :key="window.start_at" class="window-card">
            <span :class="statusClass(window.best_status)">{{ window.best_status }}</span>
            <div><small>Starts</small><strong>{{ formatDate(window.start_at) }}</strong></div>
            <span class="window-card__arrow">→</span>
            <div><small>Last candidate</small><strong>{{ formatDate(window.end_at) }}</strong></div>
          </article>
          <p v-if="!windows.windows.length" class="no-window">
            No suitable departure window was found in this search range.
          </p>
          <p class="candidate-count">{{ windows.candidates.length }} candidate departures evaluated</p>
        </div>
      </section>
    </main>

    <footer>
      <span>FlightOps · portfolio engineering project</span>
      <span>UTC storage · deterministic rules · persisted evidence</span>
    </footer>
  </div>
</template>
