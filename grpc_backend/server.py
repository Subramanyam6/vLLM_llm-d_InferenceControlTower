import argparse
import json
import os
import random
import socket
import time
from concurrent import futures

import grpc


_RPC_PATH = "/inference.InferenceService/Generate"


def _deserialize_request(raw):
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return {}


def _serialize_response(data):
    return json.dumps(data).encode("utf-8")


class InferenceService:
    def __init__(self, base_delay_s=0.12, jitter_s=0.06, error_rate=0.0):
        self.base_delay_s = float(base_delay_s)
        self.jitter_s = float(jitter_s)
        self.error_rate = float(error_rate)
        self.worker_identity = (
            os.getenv("GRPC_WORKER_ID")
            or os.getenv("HOSTNAME")
            or socket.gethostname()
            or "grpc-local"
        )

    def generate(self, request, context):
        prompt = str(request.get("prompt") or "").strip()
        if not prompt:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("prompt is required")
            return {"error": "prompt is required"}

        total_delay = self.base_delay_s + random.uniform(0.0, self.jitter_s)
        time.sleep(total_delay)
        if random.random() < self.error_rate:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("simulated grpc backend failure")
            return {"error": "simulated grpc backend failure"}

        model = request.get("model") or "fake-model"
        return {
            "text": (
                "Simulated gRPC answer:"
                f" model={model}"
                f" prompt='{prompt[:48]}'"
            ),
            "model": model,
            "transport": "grpc_http2",
            "worker_identity": self.worker_identity,
        }


def serve(bind_addr, workers, base_delay_s, jitter_s, error_rate):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=workers))
    service = InferenceService(base_delay_s, jitter_s, error_rate)
    method = grpc.unary_unary_rpc_method_handler(
        service.generate,
        request_deserializer=_deserialize_request,
        response_serializer=_serialize_response,
    )
    generic_handler = grpc.method_handlers_generic_handler(
        "inference.InferenceService",
        {"Generate": method},
    )
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_insecure_port(bind_addr)
    server.start()
    print(f"gRPC inference server listening on {bind_addr} ({_RPC_PATH})")
    server.wait_for_termination()


def main():
    parser = argparse.ArgumentParser(description="Local gRPC inference simulation server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=50051)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--base-delay", type=float, default=0.12)
    parser.add_argument("--jitter", type=float, default=0.06)
    parser.add_argument("--error-rate", type=float, default=0.0)
    args = parser.parse_args()

    serve(
        bind_addr=f"{args.host}:{args.port}",
        workers=args.workers,
        base_delay_s=args.base_delay,
        jitter_s=args.jitter,
        error_rate=args.error_rate,
    )


if __name__ == "__main__":
    main()
