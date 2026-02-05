import os
import socket
import subprocess
import sys
import time
import unittest

from core import (
    Gateway,
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
