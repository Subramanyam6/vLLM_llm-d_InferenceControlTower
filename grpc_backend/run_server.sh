#!/usr/bin/env bash
set -euo pipefail

HOST=${1:-0.0.0.0}
PORT=${2:-50051}

python3 -m grpc_backend.server --host "${HOST}" --port "${PORT}"
