# Istio Service Mesh Setup (gRPC)

This folder adds service-mesh artifacts on top of the existing project so you can route gRPC traffic through Istio.

If you want everything in one command, run:
```bash
./run_mesh_demo.sh
```
Then start the React UI:
```bash
cd frontend
npm install
npm run dev
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
```bash
./k8s_mesh/deploy.sh
```

## Port-forward the deployed gRPC service and call from app
```bash
./k8s_mesh/port_forward_ingress.sh
export GRPC_TARGET=localhost:15051
python3 app.py
```

Then pick backend `GRPC` in the UI.
