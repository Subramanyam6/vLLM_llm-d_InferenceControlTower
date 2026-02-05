#!/usr/bin/env bash
set -euo pipefail

NAMESPACE=${1:-llm-d-mesh}
SERVICE=${2:-grpc-inference-sim}
LOCAL_PORT=${3:-15051}
REMOTE_PORT=${4:-50051}

echo "Port-forwarding ${NAMESPACE}/svc/${SERVICE} on ${LOCAL_PORT}:${REMOTE_PORT}"
kubectl -n "${NAMESPACE}" port-forward "svc/${SERVICE}" "${LOCAL_PORT}:${REMOTE_PORT}"
