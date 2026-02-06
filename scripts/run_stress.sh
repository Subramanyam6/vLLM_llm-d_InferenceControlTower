#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE="smoke"
API_URL="${API_URL:-http://127.0.0.1:8000/api/submit}"
BACKEND_MODE="${BACKEND_MODE:-LLMD}"
ROUTING_MODE="${ROUTING_MODE:-least_queue}"
REQUEST_TIMEOUT="${REQUEST_TIMEOUT:-120s}"
SLO_P95_MS="${SLO_P95_MS:-2000}"
SLO_ERROR_RATE_MAX="${SLO_ERROR_RATE_MAX:-0.02}"
SCALE_VALUE="${SCALE:-5}"
DRY_RUN=0

OVERRIDE_VUS=""
OVERRIDE_RATE=""
OVERRIDE_DURATION=""
OVERRIDE_MAX_VUS=""
OVERRIDE_TARGET_REQUESTS=""
OVERRIDE_SCALE=""

usage() {
  cat <<USAGE
Usage:
  scripts/run_stress.sh --profile smoke|standard|endurance [options]

Options:
  --profile <name>           Profile name (default: smoke)
  --api-url <url>            Submit endpoint (default: http://127.0.0.1:8000/api/submit)
  --backend <mode>           Backend mode for payload (default: LLMD, only LLMD supported)
  --routing-mode <mode>      Routing mode in payload (default: least_queue)
  --vus <n>                  Override pre-allocated VUs
  --rate <n>                 Override requests per second
  --duration <time>          Override duration (for example: 120s, 20m)
  --max-vus <n>              Override max VUs
  --target-requests <n>      Override target request count metadata
  --request-timeout <time>   HTTP timeout passed to k6 (default: 120s)
  --scale <n>                Worker scale sent in submit payload (default: 5)
  --slo-p95-ms <n>           SLO threshold for p95 latency (default: 2000)
  --slo-error-rate-max <n>   SLO threshold for error rate (default: 0.02)
  --dry-run                  Print resolved profile values and exit
  -h, --help                 Show this help
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    --api-url)
      API_URL="$2"
      shift 2
      ;;
    --backend)
      BACKEND_MODE="$2"
      shift 2
      ;;
    --routing-mode)
      ROUTING_MODE="$2"
      shift 2
      ;;
    --vus)
      OVERRIDE_VUS="$2"
      shift 2
      ;;
    --rate)
      OVERRIDE_RATE="$2"
      shift 2
      ;;
    --duration)
      OVERRIDE_DURATION="$2"
      shift 2
      ;;
    --max-vus)
      OVERRIDE_MAX_VUS="$2"
      shift 2
      ;;
    --target-requests)
      OVERRIDE_TARGET_REQUESTS="$2"
      shift 2
      ;;
    --request-timeout)
      REQUEST_TIMEOUT="$2"
      shift 2
      ;;
    --scale)
      OVERRIDE_SCALE="$2"
      shift 2
      ;;
    --slo-p95-ms)
      SLO_P95_MS="$2"
      shift 2
      ;;
    --slo-error-rate-max)
      SLO_ERROR_RATE_MAX="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required" >&2
  exit 1
fi

set +e
PROFILE_ASSIGNMENTS="$(python3 - "$ROOT/load/profiles.json" "$PROFILE" <<'PY'
import json
import shlex
import sys

profiles_path = sys.argv[1]
profile_name = sys.argv[2]

with open(profiles_path, "r", encoding="utf-8") as handle:
    profiles = json.load(handle)

if profile_name not in profiles:
    print(f"invalid_profile:{profile_name}")
    sys.exit(2)

profile = profiles[profile_name]
required = ("target_requests", "vus", "rate", "duration", "max_vus")
for key in required:
    if key not in profile:
        print(f"missing_key:{key}")
        sys.exit(3)

print(f"TARGET_REQUESTS={shlex.quote(str(profile['target_requests']))}")
print(f"VUS={shlex.quote(str(profile['vus']))}")
print(f"RATE={shlex.quote(str(profile['rate']))}")
print(f"DURATION={shlex.quote(str(profile['duration']))}")
print(f"MAX_VUS={shlex.quote(str(profile['max_vus']))}")
PY
)"
profile_parse_status=$?
set -e

if [[ "$profile_parse_status" -ne 0 ]]; then
  if [[ "${PROFILE_ASSIGNMENTS}" == invalid_profile:* ]]; then
    echo "Unknown profile: ${PROFILE}" >&2
  elif [[ "${PROFILE_ASSIGNMENTS}" == missing_key:* ]]; then
    echo "Invalid profile config: ${PROFILE_ASSIGNMENTS}" >&2
  else
    echo "Failed to parse load/profiles.json for profile '${PROFILE}'" >&2
  fi
  exit 1
fi

if [[ "${PROFILE_ASSIGNMENTS}" == invalid_profile:* ]]; then
  echo "Unknown profile: ${PROFILE}" >&2
  exit 1
fi
if [[ "${PROFILE_ASSIGNMENTS}" == missing_key:* ]]; then
  echo "Invalid profile config: ${PROFILE_ASSIGNMENTS}" >&2
  exit 1
fi

eval "${PROFILE_ASSIGNMENTS}"

[[ -n "${OVERRIDE_TARGET_REQUESTS}" ]] && TARGET_REQUESTS="${OVERRIDE_TARGET_REQUESTS}"
[[ -n "${OVERRIDE_VUS}" ]] && VUS="${OVERRIDE_VUS}"
[[ -n "${OVERRIDE_RATE}" ]] && RATE="${OVERRIDE_RATE}"
[[ -n "${OVERRIDE_DURATION}" ]] && DURATION="${OVERRIDE_DURATION}"
[[ -n "${OVERRIDE_MAX_VUS}" ]] && MAX_VUS="${OVERRIDE_MAX_VUS}"
[[ -n "${OVERRIDE_SCALE}" ]] && SCALE_VALUE="${OVERRIDE_SCALE}"

BACKEND_MODE_UPPER="$(printf '%s' "${BACKEND_MODE}" | tr '[:lower:]' '[:upper:]')"
if [[ "${BACKEND_MODE_UPPER}" != "LLMD" ]]; then
  echo "This stress workflow is llm-d only. Use --backend LLMD (or omit --backend)." >&2
  exit 1
fi

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo "profile=${PROFILE}"
  echo "target_requests=${TARGET_REQUESTS}"
  echo "vus=${VUS}"
  echo "rate=${RATE}"
  echo "duration=${DURATION}"
  echo "max_vus=${MAX_VUS}"
  echo "api_url=${API_URL}"
  echo "backend=${BACKEND_MODE}"
  echo "routing_mode=${ROUTING_MODE}"
  echo "scale=${SCALE_VALUE}"
  exit 0
fi

if ! command -v k6 >/dev/null 2>&1; then
  echo "k6 is required. Install from https://k6.io/docs/get-started/installation/" >&2
  exit 1
fi

timestamp="$(date -u +"%Y%m%dT%H%M%SZ")"
run_dir="$ROOT/reports/load/$timestamp"
mkdir -p "$run_dir"

summary_raw="$run_dir/k6_summary.json"
results_json="$run_dir/results.json"
summary_md="$run_dir/summary.md"
frontend_latest_json="$ROOT/frontend/public/stress/latest.json"
frontend_latest_md="$ROOT/frontend/public/stress/latest.md"
started_at="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

echo "Running profile '${PROFILE}'"
echo "Output directory: $run_dir"

set +e
k6 run "$ROOT/load/k6_submit.js" \
  --summary-export "$summary_raw" \
  -e API_URL="$API_URL" \
  -e BACKEND="$BACKEND_MODE" \
  -e ROUTING_MODE="$ROUTING_MODE" \
  -e RATE="$RATE" \
  -e VUS="$VUS" \
  -e DURATION="$DURATION" \
  -e MAX_VUS="$MAX_VUS" \
  -e SCALE="$SCALE_VALUE" \
  -e REQUEST_TIMEOUT="$REQUEST_TIMEOUT"
k6_status=$?
set -e

ended_at="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

if [[ ! -f "$summary_raw" ]]; then
  echo "k6 did not produce a summary file at $summary_raw" >&2
  exit 1
fi

python3 "$ROOT/scripts/render_stress_report.py" \
  --summary "$summary_raw" \
  --profile "$PROFILE" \
  --target-requests "$TARGET_REQUESTS" \
  --backend "$BACKEND_MODE" \
  --target "$API_URL" \
  --output-json "$results_json" \
  --output-md "$summary_md" \
  --started-at "$started_at" \
  --ended-at "$ended_at" \
  --slo-p95-ms "$SLO_P95_MS" \
  --slo-error-rate-max "$SLO_ERROR_RATE_MAX"

mkdir -p "$(dirname "$frontend_latest_json")"
cp "$results_json" "$frontend_latest_json"
cp "$summary_md" "$frontend_latest_md"

echo "Report JSON: $results_json"
echo "Report Markdown: $summary_md"
echo "Frontend latest JSON: $frontend_latest_json"
echo "Frontend latest Markdown: $frontend_latest_md"

if [[ "$k6_status" -ne 0 ]]; then
  echo "k6 exited with status ${k6_status}" >&2
  exit "$k6_status"
fi
