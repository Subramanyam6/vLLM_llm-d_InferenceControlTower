# Istio Service Mesh Setup (gRPC)

This folder adds service-mesh artifacts on top of the existing project so you can route gRPC traffic through Istio.

If you want everything in one command, run:
```bash
MODE=GRPC ./run_all.sh
```

## What it deploys
- `grpc-inference-sim` Deployment + Service in namespace `llm-d-mesh`
- Istio `Gateway`, `VirtualService`, and `DestinationRule` for gRPC routing
- Strict mTLS policy (`PeerAuthentication`)

## Prereqs
1. Kubernetes cluster reachable by `kubectl`
2. Istio installed
3. A gRPC server image that runs `python -m grpc_backend.server`

## Configure image
By default this repo uses:
`image: inference-control-tower-grpc:local`

Build it and load it into kind:
```bash
docker build -f Dockerfile.grpc-server -t inference-control-tower-grpc:local .
kind load docker-image inference-control-tower-grpc:local --name llm-d-sim
```

## Deploy
Use `run_all.sh` (it handles build, deploy, port-forward, and app startup).
