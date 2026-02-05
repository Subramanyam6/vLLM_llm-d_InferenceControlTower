#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

IMAGE="${IMAGE:-inference-control-tower-grpc:local}"
KIND_CLUSTER="${KIND_CLUSTER:-llm-d-sim}"
MESH_NAMESPACE="${MESH_NAMESPACE:-llm-d-mesh}"
MESH_SERVICE="${MESH_SERVICE:-grpc-inference-sim}"
LOCAL_GRPC_PORT="${LOCAL_GRPC_PORT:-15051}"
REMOTE_GRPC_PORT="${REMOTE_GRPC_PORT:-50051}"

if [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
  PYTHON="${ROOT_DIR}/.venv/bin/python"
else
  PYTHON="python3"
fi

if [[ -x "${ROOT_DIR}/.venv/bin/pip" ]]; then
  PIP="${ROOT_DIR}/.venv/bin/pip"
else
  PIP="pip3"
fi

for cmd in docker kind kubectl "${PYTHON}"; do
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    echo "Missing command: ${cmd}"
    exit 1
  fi
done

if ! "${PYTHON}" - <<'PY'
import importlib.util
needed = ["grpc"]
missing = [m for m in needed if importlib.util.find_spec(m) is None]
raise SystemExit(1 if missing else 0)
PY
then
  echo "Installing Python dependencies..."
  "${PIP}" install -r requirements.txt
fi

if ! kind get clusters | grep -qx "${KIND_CLUSTER}"; then
  echo "Creating kind cluster: ${KIND_CLUSTER}"
  kind create cluster --name "${KIND_CLUSTER}"
fi

echo "Building gRPC image: ${IMAGE}"
docker build -f Dockerfile.grpc-server -t "${IMAGE}" .

echo "Loading image into kind cluster: ${KIND_CLUSTER}"
kind load docker-image "${IMAGE}" --name "${KIND_CLUSTER}"

echo "Deploying mesh resources..."
./k8s_mesh/deploy.sh

echo "Updating deployment image to ${IMAGE}"
kubectl -n "${MESH_NAMESPACE}" set image deployment/grpc-inference-sim grpc-inference-sim="${IMAGE}" >/dev/null
kubectl -n "${MESH_NAMESPACE}" rollout status deployment/grpc-inference-sim --timeout=180s

PF_LOG="$(mktemp)"
kubectl -n "${MESH_NAMESPACE}" port-forward "svc/${MESH_SERVICE}" "${LOCAL_GRPC_PORT}:${REMOTE_GRPC_PORT}" >"${PF_LOG}" 2>&1 &
PF_PID=$!

cleanup() {
  if kill -0 "${PF_PID}" >/dev/null 2>&1; then
    kill "${PF_PID}" >/dev/null 2>&1 || true
    wait "${PF_PID}" 2>/dev/null || true
  fi
  rm -f "${PF_LOG}"
}
trap cleanup EXIT INT TERM

for _ in {1..40}; do
  if (echo >/dev/tcp/127.0.0.1/"${LOCAL_GRPC_PORT}") >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done

if ! (echo >/dev/tcp/127.0.0.1/"${LOCAL_GRPC_PORT}") >/dev/null 2>&1; then
  echo "Failed to start port-forward. Log:"
  cat "${PF_LOG}"
  exit 1
fi

export GRPC_TARGET="127.0.0.1:${LOCAL_GRPC_PORT}"

echo ""
echo "Demo is ready."
echo "Path: ${ROOT_DIR}"
echo "gRPC target: ${GRPC_TARGET}"
echo "Starting API server on ${API_PORT:-8000}"
echo "Start UI:"
echo "  cd frontend"
echo "  npm install"
echo "  VITE_BACKEND=GRPC npm run dev"
echo ""

"${PYTHON}" app.py
