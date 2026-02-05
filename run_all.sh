#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="${MODE:-SIM}" # SIM | GRPC | LLMD
API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-8000}"
UI_PORT="${UI_PORT:-5173}"
MODEL_NAME="${MODEL_NAME:-fake-model}"

KIND_CLUSTER="${KIND_CLUSTER:-llm-d-sim}"
LLMD_NAMESPACE="${LLMD_NAMESPACE:-llm-d}"
LLMD_GATEWAY_SVC="${LLMD_GATEWAY_SVC:-llm-d-infra-inference-gateway-istio}"
LLMD_GATEWAY_PORT="${LLMD_GATEWAY_PORT:-80}"
LLMD_LOCAL_PORT="${LLMD_LOCAL_PORT:-8001}"

GRPC_HOST="${GRPC_HOST:-127.0.0.1}"
GRPC_PORT="${GRPC_PORT:-50051}"

port_in_use() {
  lsof -tiTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1
}

ensure_python() {
  if [[ -x "${ROOT}/.venv/bin/python" ]]; then
    PY="${ROOT}/.venv/bin/python"
  else
    PY="$(command -v python3 || true)"
  fi
  if [[ -z "${PY}" ]]; then
    echo "python3 not found" >&2
    exit 1
  fi
  if [[ ! -x "${ROOT}/.venv/bin/python" ]]; then
    "${PY}" -m venv "${ROOT}/.venv"
  fi
  "${ROOT}/.venv/bin/pip" install -r "${ROOT}/requirements.txt" >/dev/null
}

ensure_node() {
  if ! need_cmd npm; then
    echo "npm not found" >&2
    exit 1
  fi
  if [[ ! -d "${ROOT}/frontend/node_modules" ]]; then
    (cd "${ROOT}/frontend" && npm install)
  fi
}

ensure_docker() {
  if docker info >/dev/null 2>&1; then
    return 0
  fi
  if [[ "$(uname -s)" == "Darwin" ]]; then
    open -a Docker || true
    for _ in {1..30}; do
      if docker info >/dev/null 2>&1; then
        return 0
      fi
      sleep 2
    done
  fi
  echo "Docker is not running" >&2
  exit 1
}

ensure_kind_cluster() {
  if ! need_cmd kind; then
    echo "kind not found" >&2
    exit 1
  fi
  if ! kind get clusters | grep -qx "${KIND_CLUSTER}"; then
    kind create cluster --name "${KIND_CLUSTER}"
    CREATED_CLUSTER=1
  else
    CREATED_CLUSTER=0
  fi
}

ensure_istio_gateway() {
  if ! need_cmd kubectl; then
    echo "kubectl not found" >&2
    exit 1
  fi
  if ! need_cmd helm; then
    echo "helm not found" >&2
    exit 1
  fi
  if ! need_cmd istioctl; then
    echo "istioctl not found" >&2
    exit 1
  fi

  kubectl apply -k "https://github.com/kubernetes-sigs/gateway-api/config/crd?ref=v1.4.0" >/dev/null
  istioctl install --set profile=minimal -y >/dev/null

  kubectl get ns "${LLMD_NAMESPACE}" >/dev/null 2>&1 || kubectl create ns "${LLMD_NAMESPACE}" >/dev/null

  helm repo add llm-d-infra https://llm-d-incubation.github.io/llm-d-infra/ >/dev/null
  helm repo add llm-d-modelservice https://llm-d-incubation.github.io/llm-d-modelservice/ >/dev/null
  helm repo update >/dev/null

  helm upgrade --install llm-d-infra llm-d-infra/llm-d-infra \
    --namespace "${LLMD_NAMESPACE}" --create-namespace --version v1.3.6 >/dev/null

  cat <<YAML >/tmp/llm-d-modelservice-values.yaml
modelArtifacts:
  name: ${MODEL_NAME}
  uri: "hf://${MODEL_NAME}"
  size: 5Mi
accelerator:
  type: cpu
routing:
  proxy:
    enabled: false
decode:
  replicas: 2
  containers:
    - name: "vllm"
      image: "ghcr.io/llm-d/llm-d-inference-sim:latest"
      modelCommand: imageDefault
      args:
        - "--model"
        - "${MODEL_NAME}"
        - "--port"
        - "8000"
        - "--served-model-name"
        - "${MODEL_NAME}"
prefill:
  create: false
YAML

  helm upgrade --install llm-d-modelservice llm-d-modelservice/llm-d-modelservice \
    --namespace "${LLMD_NAMESPACE}" --version v0.4.5 -f /tmp/llm-d-modelservice-values.yaml >/dev/null

  kubectl rollout status deployment/llm-d-modelservice-decode -n "${LLMD_NAMESPACE}" --timeout=180s >/dev/null

  cat <<YAML | kubectl apply -f - >/dev/null
apiVersion: v1
kind: Service
metadata:
  name: llm-d-modelservice-svc
  namespace: ${LLMD_NAMESPACE}
spec:
  selector:
    llm-d.ai/inference-serving: "true"
    llm-d.ai/role: "decode"
  ports:
    - name: http
      port: 8000
      targetPort: 8000
YAML

  cat <<YAML | kubectl apply -f - >/dev/null
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: llm-d-inference-route
  namespace: ${LLMD_NAMESPACE}
spec:
  parentRefs:
    - name: llm-d-infra-inference-gateway
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: llm-d-modelservice-svc
          port: 8000
YAML
}

start_api() {
  DEFAULT_BACKEND="${1}" ENABLE_LLMD_LOCAL="${2:-}" LLMD_HTTP_URL="${3:-}" \
    MODEL_NAME="${MODEL_NAME}" API_HOST="${API_HOST}" API_PORT="${API_PORT}" \
    "${ROOT}/.venv/bin/python" "${ROOT}/app.py" > /tmp/ict_api.log 2>&1 &
  API_PID=$!
}

start_grpc() {
  "${ROOT}/.venv/bin/python" -m grpc_backend.server --host "${GRPC_HOST}" --port "${GRPC_PORT}" \
    > /tmp/ict_grpc.log 2>&1 &
  GRPC_PID=$!
}

start_ui() {
  local backend="$1"
  (cd "${ROOT}/frontend" && \
    VITE_BACKEND="${backend}" \
    VITE_ENABLE_LLMD="${VITE_ENABLE_LLMD:-}" \
    VITE_DISABLE_GRPC="${VITE_DISABLE_GRPC:-}" \
    VITE_LOCK_MODE="${VITE_LOCK_MODE:-}" \
    npm run dev -- --port "${UI_PORT}")
}

cleanup() {
  [[ -n "${PF_PID:-}" ]] && kill "${PF_PID}" >/dev/null 2>&1 || true
  [[ -n "${API_PID:-}" ]] && kill "${API_PID}" >/dev/null 2>&1 || true
  [[ -n "${GRPC_PID:-}" ]] && kill "${GRPC_PID}" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

for p in "${API_PORT}" "${UI_PORT}"; do
  if port_in_use "${p}"; then
    echo "Port ${p} is already in use." >&2
    exit 1
  fi
done

ensure_python
ensure_node

case "${MODE}" in
  SIM)
    start_api "SIM"
    start_ui "SIM"
    ;;
  GRPC)
    for p in "${GRPC_PORT}"; do
      if port_in_use "${p}"; then
        echo "Port ${p} is already in use." >&2
        exit 1
      fi
    done
    start_grpc
    GRPC_TARGET="${GRPC_HOST}:${GRPC_PORT}" DEFAULT_BACKEND="GRPC" \
      GRPC_TARGET="${GRPC_TARGET}" "${ROOT}/.venv/bin/python" "${ROOT}/app.py" \
      > /tmp/ict_api.log 2>&1 &
    API_PID=$!
    VITE_LOCK_MODE=1 start_ui "GRPC"
    ;;
  LLMD)
    if port_in_use "${LLMD_LOCAL_PORT}"; then
      echo "Port ${LLMD_LOCAL_PORT} is already in use." >&2
      exit 1
    fi
    ensure_docker
    ensure_kind_cluster
    ensure_istio_gateway
    kubectl -n "${LLMD_NAMESPACE}" port-forward "svc/${LLMD_GATEWAY_SVC}" "${LLMD_LOCAL_PORT}:${LLMD_GATEWAY_PORT}" \
      > /tmp/ict_llmd_pf.log 2>&1 &
    PF_PID=$!
    sleep 2
    start_api "LLMD" "1" "http://localhost:${LLMD_LOCAL_PORT}"
    VITE_ENABLE_LLMD=1 VITE_LOCK_MODE=1 start_ui "LLMD"
    ;;
  *)
    echo "Unknown MODE: ${MODE} (use SIM|GRPC|LLMD)" >&2
    exit 1
    ;;
esac
