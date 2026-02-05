# llm-d Inference-Sim (Local)

The app no longer includes `EXTERNAL_HTTP` backend mode.
Use gRPC mode instead via:
- `./run_mesh_demo.sh` (one command)
- or `k8s_mesh/` manifests and helper scripts.

## Legacy Port-Forward (HTTP)
This helper remains only as a reference for legacy HTTP inference-sim setups:
```bash
./k8s_llmd/port_forward_example.sh
```
