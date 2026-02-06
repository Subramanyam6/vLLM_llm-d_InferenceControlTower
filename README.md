---
title: VLLM Llm-d InferenceControlTower
colorFrom: pink
colorTo: purple
sdk: docker
pinned: false
---

# Inference Control Tower

## Overview
A lightweight control tower UI + gateway that routes LLM requests across workers with cache-aware and queue-aware logic. It demonstrates routing, retries, rate limits, chaos injection, and observability patterns without requiring a full GPU cluster.

Live demo (HF Spaces): `https://huggingface.co/spaces/Subramanyam6/vLLM_llm-d_InferenceControlTower`

## Quick Start (Local, All Core Modes)
```bash
git clone https://huggingface.co/spaces/Subramanyam6/vLLM_llm-d_InferenceControlTower
cd vLLM_llm-d_InferenceControlTower

./run_all.sh
```

This starts API + UI + local gRPC simulator + local llm-d path.
Open `http://127.0.0.1:5173`.

## Mode Matrix

### `SIM` (light-weight demo)
- No local services required.
- Everything runs inside the control tower process.

### `GRPC` (local)
```bash
MODE=GRPC ./run_all.sh
```
- Uses local gRPC backend workers.
- UI is locked to gRPC in this mode to avoid misrouted traffic.

### `LLMD` (local)
```bash
MODE=LLMD ./run_all.sh
```
- Uses local llm-d gateway workflow.
- Requests pass through SGLang first, then continue to llm-d (`ENABLE_SGLANG_FRONT=1` by default).
- UI is locked to llm-d in this mode.

## Hosted (HF Spaces) Behavior
Hosted deployments stay light-weight and cost-safe:
- `SIM` only
- `gRPC` and `llm-d` are disabled

## Environment Flags

Backend flags:
- `DISABLE_GRPC=1` to force SIM fallback
- `ENABLE_LLMD_LOCAL=1` to allow llm-d mode
- `ENABLE_SGLANG_FRONT=1` to route llm-d requests through SGLang first
- `SGLANG_HTTP_URL=http://127.0.0.1:30000`
- `VLLM_HTTP_URL=http://127.0.0.1:8001` (optional OpenAI HTTP target for gRPC track)

Frontend flags:
- `VITE_ENABLE_LLMD=1`
- `VITE_DISABLE_GRPC=1`
- `VITE_LOCK_MODE=1`

## Offline Stress Testing (k6)

### Profiles
- `smoke`: 100,000 requests
- `standard`: 1,000,000 requests
- `endurance`: 5,000,000 requests

Profile definitions live in `load/profiles.json`.

### Run a profile
```bash
scripts/run_stress.sh --profile smoke
```
Default stress payload scale is `5` workers (A-E).

Optional overrides:
```bash
scripts/run_stress.sh --profile standard \
  --backend LLMD \
  --api-url http://127.0.0.1:8000/api/submit \
  --rate 1200 --vus 300 --duration 900s --scale 5
```

The stress workflow is llm-d focused; non-LLMD backends are rejected by `run_stress.sh`.

Dry-run config validation:
```bash
scripts/run_stress.sh --profile endurance --dry-run
```

### Report output
Each run writes:
- `reports/load/<timestamp>/results.json`
- `reports/load/<timestamp>/summary.md`

`results.json` includes:
- profile
- total attempted/succeeded/failed
- error rate
- p50/p95/p99 latency
- throughput (req/s)
- backend mode
- target URL
- start/end timestamps
- worker distribution raw counts for A-E (`worker_distribution`)
- worker distribution percentages for A-E (`worker_distribution_pct`)
- raw extras (`other`, `missing`, `counted`) in `worker_distribution_meta`

For non-SIM backends, the API now emits `worker_identity` when upstream identity is available
(response body or headers). If identity is unavailable, `selected_worker` may be null and will
be counted as `missing` in load reports.

`summary.md` includes:
- run metadata
- key metrics table
- worker distribution table for A-E
- SLO pass/fail section
- top failure reasons

## Optional: OpenTelemetry Console Exporter
```bash
OTEL=1 python app.py
```

## Tiny In-Process Benchmark
```bash
python bench.py
```

## Service Mesh Artifacts
- `k8s_mesh/`
- `k8s_llmd/`

## Repo Structure
- `app.py`: API server + UI static host
- `core.py`: gateway, routing, workers, retries, OpenAI HTTP bridges
- `frontend/`: React UI (Vite)
- `grpc_backend/server.py`: local gRPC inference server
- `load/`: k6 script + load profiles
- `scripts/`: stress runner + report renderer
- `tests/`: unit/integration tests
