#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STACK_FILE="$ROOT/observability/docker-compose.yml"
ACTION="${1:-up}"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required" >&2
  exit 1
fi

compose_cmd=(docker compose -f "$STACK_FILE")

case "$ACTION" in
  up)
    "${compose_cmd[@]}" up -d
    echo "Observability stack started:"
    echo "  Prometheus: http://127.0.0.1:9090"
    echo "  Grafana:    http://127.0.0.1:3001 (admin/admin)"
    echo "  Jaeger:     http://127.0.0.1:16686"
    ;;
  down)
    "${compose_cmd[@]}" down
    ;;
  status|ps)
    "${compose_cmd[@]}" ps
    ;;
  logs)
    "${compose_cmd[@]}" logs --tail=120
    ;;
  *)
    echo "Usage: scripts/observability_stack.sh [up|down|status|logs]" >&2
    exit 1
    ;;
esac
