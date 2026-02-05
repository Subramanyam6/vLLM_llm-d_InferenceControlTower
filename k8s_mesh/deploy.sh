#!/usr/bin/env bash
set -euo pipefail

kubectl apply -f k8s_mesh/namespace.yaml
kubectl apply -f k8s_mesh/grpc-inference-sim.yaml
kubectl apply -f k8s_mesh/istio-routing.yaml

echo "Waiting for grpc-inference-sim rollout..."
kubectl -n llm-d-mesh rollout status deployment/grpc-inference-sim --timeout=180s

echo "Mesh stack deployed."
