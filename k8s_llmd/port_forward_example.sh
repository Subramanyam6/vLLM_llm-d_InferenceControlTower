#!/usr/bin/env bash
set -euo pipefail

# Example usage: ./port_forward_example.sh my-namespace my-service 8000 8000
NAMESPACE=${1:-default}
SERVICE=${2:-llm-d-inference-sim}
LOCAL_PORT=${3:-8000}
REMOTE_PORT=${4:-8000}

echo "Port-forwarding svc/${SERVICE} in ${NAMESPACE} on ${LOCAL_PORT}:${REMOTE_PORT}"
kubectl -n "${NAMESPACE}" port-forward "svc/${SERVICE}" "${LOCAL_PORT}:${REMOTE_PORT}"
