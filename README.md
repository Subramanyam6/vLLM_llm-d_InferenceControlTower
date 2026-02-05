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

./run_all.sh
```
This starts the API and UI. Open `http://127.0.0.1:5173`.

## gRPC Mode (Local, Simulated)
One command:
```bash
MODE=GRPC ./run_all.sh
```
The UI is locked to gRPC for this run to avoid misrouted traffic.

## llm-d Mode (Local Only, Official Simulator)
This uses the official `llm-d-inference-sim` image behind the llm-d gateway.
Enable it only for local testing:
```bash
MODE=LLMD ./run_all.sh
```
The script enables the UI mode automatically.
The UI is locked to llm-d for this run to avoid gRPC errors.

## vLLM Dev Image (Local, Real Backend)
Run the official vLLM OpenAI-compatible server (requires Docker and a supported GPU):
```bash
docker run --runtime nvidia --gpus all \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -p 8001:8000 \
  --ipc=host \
  vllm/vllm-openai:latest \
  --model Qwen/Qwen3-0.6B
```
Then point the gateway at the vLLM HTTP server:
```bash
export VLLM_HTTP_URL=http://127.0.0.1:8001
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
Manifests live in `k8s_mesh/` and `k8s_llmd/` (no standalone scripts).

## Repo Structure
- `app.py`: API server + UI static file host
- `core.py`: gateway, routing, workers, cache, chaos, metrics, traces
- `bench.py`: latency benchmark (no network)
- `requirements.txt`
- `grpc_backend/server.py`: local gRPC inference server (HTTP/2)
- `frontend/`: React UI (Vite)
- `k8s_mesh/`: Istio service mesh manifests
- `k8s_llmd/README.md`: minimal llm-d inference-sim notes
