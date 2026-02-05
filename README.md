---
title: VLLM Llm-d InferenceControlTower
emoji: 📉
colorFrom: pink
colorTo: purple
sdk: docker
pinned: false
---

# Inference Control Tower

## What Problem This Solves
This demo shows how a single gateway can safely route LLM requests across multiple workers, balancing latency, cache reuse, and reliability. It mirrors common ML infra needs: rate limiting, retries, timeouts, cache-aware routing, and basic observability.

## Internal Routing (Automatic)
The UI is intentionally simple now: choose mode and send a prompt.
Internally, the gateway still routes requests with queue-aware/cache-aware logic.

## Run Locally (Light-weight Demo Mode)
```bash
python app.py
```
This uses a threaded simulation backend with no GPU.
In the UI backend dropdown, choose `Light-weight Demo`.
By default, demo worker count auto-aligns to Kubernetes deployment replicas (currently `2`).
Start the React UI:
```bash
cd frontend
npm install
VITE_BACKEND=SIM npm run dev
```
Then open `http://127.0.0.1:5173`.

## Run gRPC over HTTP/2 Backend
Start the local gRPC simulation server in one terminal:
```bash
python -m grpc_backend.server --host 127.0.0.1 --port 50051
```

Start the UI in another terminal and target gRPC:
```bash
export GRPC_TARGET=127.0.0.1:50051
python app.py
```
Then start the UI with:
```bash
cd frontend
VITE_BACKEND=GRPC npm run dev
```

## Run on Hugging Face Spaces
This repo uses `app.py` as the entrypoint; Spaces will auto-detect it.

## Optional: OpenTelemetry Console Exporter
```bash
OTEL=1 python app.py
```
Spans are printed to stdout for quick debugging.

## Tiny Benchmark
```bash
python bench.py
```
Prints p50/p95 latency for each routing mode using the in-process gateway.

## Service Mesh (Istio) Artifacts
This repo now includes Istio gRPC mesh manifests in `k8s_mesh/`:
- `k8s_mesh/grpc-inference-sim.yaml`: deployment + service
- `k8s_mesh/istio-routing.yaml`: `Gateway`, `VirtualService`, `DestinationRule`, `PeerAuthentication`
- `k8s_mesh/deploy.sh`: apply everything
- `k8s_mesh/port_forward_ingress.sh`: expose gRPC service locally

One command demo:
```bash
./run_mesh_demo.sh
```
This does build + load + deploy + port-forward + launches the API server.
Run the React UI with `npm run dev` in `frontend/`.

Quick start:
```bash
docker build -f Dockerfile.grpc-server -t inference-control-tower-grpc:local .
kind load docker-image inference-control-tower-grpc:local --name llm-d-sim
./k8s_mesh/deploy.sh
./k8s_mesh/port_forward_ingress.sh
export GRPC_TARGET=localhost:15051
python app.py
```

## Unit Tests
```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Repo Structure
- `app.py`: UI and wiring
- `core.py`: gateway, routing, workers, cache, chaos, metrics, traces
- `bench.py`: latency benchmark (no network)
- `requirements.txt`
- `grpc_backend/server.py`: local gRPC inference server (HTTP/2 transport)
- `frontend/`: React UI (Vite)
- `k8s_mesh/`: Istio service mesh manifests and helper scripts
- `run_mesh_demo.sh`: one-command local mesh demo launcher
- `k8s_llmd/README.md`: minimal llm-d inference-sim notes
- `k8s_llmd/port_forward_example.sh`: sample port-forward script
