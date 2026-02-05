---
title: VLLM Llm-d InferenceControlTower
colorFrom: pink
colorTo: purple
sdk: docker
pinned: false
---

# Inference Control Tower

## Overview
A lightweight control tower UI + gateway that routes LLM requests across workers with cache-aware and queue-aware logic. It demonstrates routing, retries, rate limits, and basic observability without requiring a GPU cluster.

## Quick Start (Local, SIM Mode)
```bash
git clone https://huggingface.co/spaces/Subramanyam6/vLLM_llm-d_InferenceControlTower
cd vLLM_llm-d_InferenceControlTower

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python app.py
```
Start the UI:
```bash
cd frontend
npm install
VITE_BACKEND=SIM npm run dev
```
Open `http://127.0.0.1:5173`.

## gRPC Mode (Local)
Start the local gRPC server:
```bash
python -m grpc_backend.server --host 127.0.0.1 --port 50051
```
Start the API server:
```bash
export GRPC_TARGET=127.0.0.1:50051
python app.py
```
Start the UI:
```bash
cd frontend
VITE_BACKEND=GRPC npm run dev
```

## Optional: OpenTelemetry Console Exporter
```bash
OTEL=1 python app.py
```

## Tiny Benchmark
```bash
python bench.py
```

## Service Mesh (Istio) Artifacts
Manifests and helper scripts live in `k8s_mesh/` and `k8s_llmd/`.

## Repo Structure
- `app.py`: API server + UI static file host
- `core.py`: gateway, routing, workers, cache, chaos, metrics, traces
- `bench.py`: latency benchmark (no network)
- `requirements.txt`
- `grpc_backend/server.py`: local gRPC inference server (HTTP/2)
- `frontend/`: React UI (Vite)
- `k8s_mesh/`: Istio service mesh manifests and helper scripts
- `run_mesh_demo.sh`: one-command local mesh demo launcher
- `k8s_llmd/README.md`: minimal llm-d inference-sim notes
