import io
import json
import os
import socket
import subprocess
import sys
import time
import unittest
import urllib.error
from unittest import mock

from core import (
    Gateway,
    _extract_worker_identity,
    _fingerprint,
    _parse_grpc_response,
    format_trace,
)


class CoreTests(unittest.TestCase):
    def test_fingerprint_stable(self):
        self.assertEqual(_fingerprint("hello"), _fingerprint("hello"))
        self.assertNotEqual(_fingerprint("hello"), _fingerprint("world"))

    def test_rate_limit(self):
        gw = Gateway(worker_count=1, rate_limit_per_min=1, retries=0)
        ok = gw.handle("hi", "SIM", "round_robin")
        self.assertIsNone(ok["error"])
        blocked = gw.handle("hi again", "SIM", "round_robin")
        self.assertEqual(blocked["error"], "rate_limited")

    def test_cache_hit_single_worker(self):
        gw = Gateway(worker_count=1, rate_limit_per_min=1000, retries=0)
        first = gw.handle("repeat", "SIM", "cache_aware")
        self.assertIsNone(first["error"])
        second = gw.handle("repeat", "SIM", "cache_aware")
        self.assertTrue(second["cache_hit"])

    def test_parse_grpc_response(self):
        self.assertEqual(_parse_grpc_response({"text": "hello"}), "hello")
        self.assertEqual(_parse_grpc_response({"response": "hi"}), "hi")
        self.assertIn("42", _parse_grpc_response(42))

    def test_format_trace(self):
        now = time.time()
        trace = [(now, "received"), (now + 0.01, "responded")]
        out = format_trace(trace)
        self.assertIn("received", out)
        self.assertIn("responded", out)

    def test_extract_worker_identity_body_and_headers(self):
        identity = _extract_worker_identity(
            {"worker_identity": "pod-a"},
            {"x-upstream-host": "10.0.0.5:8000"},
        )
        self.assertEqual(identity, "pod-a")
        header_only = _extract_worker_identity(
            {},
            {"x-upstream-host": "10.0.0.6:8000"},
        )
        self.assertEqual(header_only, "10.0.0.6:8000")

    def test_sglang_handler_success(self):
        gw = Gateway(worker_count=1, rate_limit_per_min=1000, retries=0)
        rewrite_payload = {
            "choices": [{"message": {"role": "assistant", "content": "rewritten prompt"}}]
        }
        llmd_payload = {
            "choices": [{"message": {"role": "assistant", "content": "llmd final"}}]
        }

        class FakeHeaders:
            def __init__(self, data):
                self._data = data

            def items(self):
                return self._data.items()

        class FakeResponse:
            def __init__(self, payload, headers=None):
                self._payload = payload
                self.headers = FakeHeaders(headers or {})

            def __enter__(self_inner):
                return self_inner

            def __exit__(self_inner, exc_type, exc, tb):
                return False

            def read(self_inner):
                return json.dumps(self_inner._payload).encode("utf-8")

        with mock.patch.dict(
            os.environ,
            {
                "SGLANG_HTTP_URL": "http://127.0.0.1:30000",
                "LLMD_HTTP_URL": "http://127.0.0.1:8000",
            },
        ):
            with mock.patch(
                "urllib.request.urlopen",
                side_effect=[
                    FakeResponse(rewrite_payload, {"x-worker-id": "pod-sglang-1"}),
                    FakeResponse(llmd_payload, {"x-worker-id": "pod-llmd-1"}),
                ],
            ):
                res = gw.handle("hello sglang", "SGLANG", "round_robin")

        self.assertIsNone(res["error"])
        self.assertEqual(res["worker_id"], "pod-llmd-1")
        self.assertEqual(res["reason"]["mode"], "llm-d+sglang")
        self.assertEqual(res["reason"]["sglang_identity"], "pod-sglang-1")
        self.assertEqual(res["text"], "llmd final")

    def test_sglang_handler_http_error_includes_body(self):
        gw = Gateway(worker_count=1, rate_limit_per_min=1000, retries=0)
        err = urllib.error.HTTPError(
            url="http://127.0.0.1:30000/v1/chat/completions",
            code=503,
            msg="service unavailable",
            hdrs=None,
            fp=io.BytesIO(b"upstream overloaded"),
        )

        with mock.patch.dict(os.environ, {"SGLANG_HTTP_URL": "http://127.0.0.1:30000"}):
            with mock.patch("urllib.request.urlopen", side_effect=err):
                res = gw.handle("hello sglang", "SGLANG", "round_robin")

        self.assertIsNotNone(res["error"])
        self.assertIn("sglang_front_error", res["error"])
        self.assertIn("503", res["error"])
        self.assertIn("upstream overloaded", res["error"])


class GrpcIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import grpc  # noqa: F401
        except Exception as exc:
            raise unittest.SkipTest(f"grpcio not available: {exc}")

        cls._port = cls._find_free_port()
        env = os.environ.copy()
        env.setdefault("PYTHONPATH", os.getcwd())
        cls._proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "grpc_backend.server",
                "--host",
                "127.0.0.1",
                "--port",
                str(cls._port),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        cls._wait_for_port("127.0.0.1", cls._port, timeout_s=8.0)

    @classmethod
    def tearDownClass(cls):
        proc = getattr(cls, "_proc", None)
        if not proc:
            return
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()

    @staticmethod
    def _find_free_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return sock.getsockname()[1]

    @staticmethod
    def _wait_for_port(host, port, timeout_s):
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.5)
                if sock.connect_ex((host, port)) == 0:
                    return
            time.sleep(0.1)
        raise RuntimeError(f"timed out waiting for {host}:{port}")

    def test_grpc_backend_path(self):
        gw = Gateway(worker_count=1, rate_limit_per_min=1000, retries=0)
        res = gw.handle(
            "hello grpc",
            "GRPC",
            "round_robin",
            grpc_target=f"127.0.0.1:{self._port}",
        )
        self.assertIsNone(res["error"])
        self.assertEqual(res["worker_id"], "grpc")
        self.assertEqual(res["reason"]["mode"], "grpc")
        self.assertIn("Simulated gRPC answer:", res["text"])


if __name__ == "__main__":
    unittest.main()
