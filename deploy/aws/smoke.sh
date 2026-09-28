#!/usr/bin/env bash
set -euo pipefail

base_url=${BASE_URL:?Set BASE_URL to the deployed HTTPS URL}
base_url=${base_url%/}
suffix=$(date -u +%Y%m%d%H%M%S)
departure=$(date -u -d "+1 day" +%Y-%m-%dT%H:00:00Z)

echo "Checking health..."
curl --retry 12 --retry-delay 5 --retry-all-errors   --fail --silent --show-error "$base_url/health/ready" | jq .

aircraft_id=$(curl --fail --silent --show-error   -X POST "$base_url/api/v1/aircraft"   -H "Content-Type: application/json"   -d "{
    \"name\": \"Deployment verification $suffix\",
    \"max_wind_speed_mps\": 12,
    \"max_gust_speed_mps\": 18,
    \"max_precipitation_mm_per_hour\": 2,
    \"min_temperature_c\": -10,
    \"max_temperature_c\": 45
  }" | jq -r .id)

mission_id=$(curl --fail --silent --show-error   -X POST "$base_url/api/v1/missions"   -H "Content-Type: application/json"   -d "{
    \"aircraft_id\": \"$aircraft_id\",
    \"name\": \"Deployment smoke route\",
    \"planned_departure_at\": \"$departure\",
    \"waypoints\": [
      {\"latitude\": 36.8065, \"longitude\": 10.1815},
      {\"latitude\": 36.8500, \"longitude\": 10.2500}
    ]
  }" | jq -r .id)

assessment=$(curl --fail --silent --show-error   -X POST "$base_url/api/v1/missions/$mission_id/assessments"   -H "Content-Type: application/json"   -d "{}")

echo "$assessment" | jq '{
  status,
  limiting_factor,
  rule_version,
  observations: (.snapshot.observations | length)
}'

assessment_id=$(echo "$assessment" | jq -r .id)
curl --fail --silent --show-error   "$base_url/api/v1/assessments/$assessment_id" >/dev/null

echo "Deployment smoke test passed."
