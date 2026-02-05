#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PY="${PYTHON:-}"
if [[ -z "${PY}" ]]; then
  if [[ -x "${ROOT}/.venv/bin/python" ]]; then
    PY="${ROOT}/.venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PY="python3"
  elif command -v python >/dev/null 2>&1; then
    PY="python"
  else
    echo "python not found" >&2
    exit 1
  fi
fi

GRPC_HOST="${GRPC_HOST:-127.0.0.1}"
GRPC_PORT="${GRPC_PORT:-50051}"
API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-8000}"
UI_PORT="${UI_PORT:-5173}"
GRPC_TARGET="${GRPC_HOST}:${GRPC_PORT}"

port_in_use() {
  lsof -tiTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

for p in "${GRPC_PORT}" "${API_PORT}" "${UI_PORT}"; do
  if port_in_use "${p}"; then
    echo "Port ${p} is already in use. Stop it or set a different port." >&2
    exit 1
  fi
done

"${PY}" -m grpc_backend.server --host "${GRPC_HOST}" --port "${GRPC_PORT}" \
  > /tmp/ict_grpc.log 2>&1 &
GRPC_PID=$!

GRPC_TARGET="${GRPC_TARGET}" API_HOST="${API_HOST}" API_PORT="${API_PORT}" \
  "${PY}" app.py > /tmp/ict_api.log 2>&1 &
API_PID=$!

cleanup() {
  kill -9 "${API_PID}" "${GRPC_PID}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

cd "${ROOT}/frontend"
if [[ ! -d node_modules ]]; then
  npm install
fi

API_HOST="${API_HOST}" API_PORT="${API_PORT}" VITE_BACKEND="${VITE_BACKEND:-GRPC}" \
  npm run dev -- --port "${UI_PORT}"
