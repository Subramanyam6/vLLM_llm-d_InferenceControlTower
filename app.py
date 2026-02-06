import hashlib
import json
import mimetypes
import os
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

from core import Gateway


_PORT = int(
    os.getenv("PORT") or os.getenv("API_PORT") or os.getenv("APP_PORT", "8000")
)
_HOST = os.getenv("API_HOST") or os.getenv("APP_HOST") or (
    "0.0.0.0" if os.getenv("PORT") else "127.0.0.1"
)
_MESH_NAMESPACE = os.getenv("MESH_NAMESPACE", "llm-d-mesh")
_MESH_DEPLOYMENT = os.getenv("MESH_DEPLOYMENT", "grpc-inference-sim")
_LLMD_NAMESPACE = os.getenv("LLMD_NAMESPACE", "llm-d")
_LLMD_DEPLOYMENT = os.getenv("LLMD_DEPLOYMENT", "llm-d-modelservice-decode")
_ROUTING_MODE = os.getenv("ROUTING_MODE", "least_queue")
_DEFAULT_WORKERS = max(1, int(os.getenv("DEFAULT_SIM_WORKERS", "2")))
_DEFAULT_RATE_LIMIT = int(os.getenv("DEFAULT_RATE_LIMIT", "60"))
_DEFAULT_SCALE = int(os.getenv("DEFAULT_SCALE", "3"))
_DISABLE_GRPC = str(os.getenv("DISABLE_GRPC", "")).lower() in ("1", "true", "yes")
_ENABLE_LLMD = str(os.getenv("ENABLE_LLMD_LOCAL", "")).lower() in ("1", "true", "yes")
_STATIC_DIR = os.path.abspath(
    os.getenv("STATIC_DIR", os.path.join(os.path.dirname(__file__), "frontend", "dist"))
)
_STATIC_INDEX = os.path.join(_STATIC_DIR, "index.html")
_HAVE_STATIC = os.path.isfile(_STATIC_INDEX)
_REPORTS_LOAD_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "reports", "load")
)


def _detect_mesh_replicas(default_replicas):
    try:
        out = subprocess.run(
            [
                "kubectl",
                "-n",
                _MESH_NAMESPACE,
                "get",
                "deployment",
                _MESH_DEPLOYMENT,
                "-o",
                "jsonpath={.spec.replicas}",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=2,
        )
        replicas = int((out.stdout or "").strip() or "0")
        return max(1, replicas)
    except Exception:
        return int(default_replicas)


_WORKERS = max(
    1,
    int(os.getenv("DEMO_WORKERS", str(_detect_mesh_replicas(_DEFAULT_WORKERS)))),
)
gateway = Gateway(worker_count=_WORKERS)
_STATE = {
    "backend": os.getenv("DEFAULT_BACKEND", "SIM"),
    "scale": _DEFAULT_SCALE,
    "scale_status": "local",
    "scale_error": None,
    "routing_mode": _ROUTING_MODE,
    "kill_worker": False,
    "delay_s": 0.0,
    "error_rate": 0.0,
    "rate_limit": _DEFAULT_RATE_LIMIT,
}


def _normalize_backend(backend):
    backend_raw = str(backend or "").strip()
    backend_upper = backend_raw.upper()

    if backend_raw == "Light-weight Demo" or backend_upper == "SIM":
        next_backend = "SIM"
    elif backend_upper in ("LLMD", "SGLANG") or backend_raw in (
        "llm-d (local)",
        "sglang (local)",
    ):
        next_backend = "LLMD"
    elif backend_upper == "GRPC" or backend_raw in ("gRPC", "gRPC (local)"):
        next_backend = "GRPC"
    else:
        next_backend = "GRPC"

    if _DISABLE_GRPC and next_backend == "GRPC":
        return "SIM"
    if next_backend == "LLMD" and not _ENABLE_LLMD:
        return "SIM"
    return next_backend


def _mode_label(backend_value):
    if backend_value == "SIM":
        return "Light-weight Demo"
    if backend_value == "LLMD":
        return "llm-d (local)"
    return "gRPC (local)"


_STATE["backend"] = _normalize_backend(_STATE["backend"])
gateway.set_worker_count(_STATE["scale"])


def _set_rate_limit(value):
    try:
        value = max(1, int(value))
    except Exception:
        return
    if hasattr(gateway, "set_rate_limit"):
        gateway.set_rate_limit(value)


def _scale_workers(target, backend_value):
    try:
        target = max(1, int(target))
    except Exception:
        return _WORKERS, "error", "invalid scale"

    if backend_value == "GRPC":
        try:
            subprocess.run(
                [
                    "kubectl",
                    "-n",
                    _MESH_NAMESPACE,
                    "scale",
                    f"deployment/{_MESH_DEPLOYMENT}",
                    f"--replicas={target}",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
            )
            return target, "ok", None
        except subprocess.TimeoutExpired:
            return target, "error", "kubectl timeout"
        except subprocess.CalledProcessError as exc:
            msg = (exc.stderr or exc.stdout or "").strip()
            return target, "error", msg or "kubectl failed"
        except Exception as exc:
            return target, "error", str(exc)
    if backend_value == "LLMD":
        try:
            subprocess.run(
                [
                    "kubectl",
                    "-n",
                    _LLMD_NAMESPACE,
                    "scale",
                    f"deployment/{_LLMD_DEPLOYMENT}",
                    f"--replicas={target}",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
            )
            return target, "ok", None
        except subprocess.TimeoutExpired:
            return target, "error", "kubectl timeout"
        except subprocess.CalledProcessError as exc:
            msg = (exc.stderr or exc.stdout or "").strip()
            return target, "error", msg or "kubectl failed"
        except Exception as exc:
            return target, "error", str(exc)
    return target, "local", None


def _worker_label(idx):
    return chr(ord("A") + idx) if idx < 26 else str(idx + 1)


def _worker_label_from_identity(identity, scale):
    scale = max(1, int(scale))
    digest = hashlib.md5(identity.encode("utf-8")).hexdigest()
    idx = int(digest[:8], 16) % scale
    return _worker_label(idx)


def _extract_worker_identity_from_result(result):
    reason = result.get("reason") or {}
    worker_identity = str(reason.get("worker_identity") or "").strip()
    if worker_identity:
        return worker_identity
    worker_id = result.get("worker_id")
    if isinstance(worker_id, str):
        value = worker_id.strip()
        if value:
            return value
    return ""


def _resolve_selected_worker(result, backend_value, scale):
    worker_id = result.get("worker_id")
    if isinstance(worker_id, int):
        return _worker_label(worker_id % max(1, int(scale)))
    if isinstance(worker_id, str) and worker_id.isdigit():
        return _worker_label(int(worker_id) % max(1, int(scale)))

    if backend_value == "SIM":
        return _worker_label(0)

    worker_identity = _extract_worker_identity_from_result(result)
    if not worker_identity:
        return None

    # Generic markers mean upstream identity is still unknown.
    if worker_identity.lower() in {"grpc", "llm-d", "sglang", "vllm", "vllm_http"}:
        return None

    return _worker_label_from_identity(worker_identity, scale)


def _worker_status(worker):
    if worker["health"] != "UP":
        return "DOWN"
    if worker["p95_ms"] >= 1200:
        return "SLOW"
    return "HEALTHY"


def _build_why(worker, reason=None):
    if not worker:
        return []

    reason = reason or {}
    cache_hit = bool(reason.get("cache_hit"))
    cache_score = 5 if cache_hit else (5 if worker["cache_warmth"] >= 0.4 else 0)
    cache_note = "Cache hit on this prompt" if cache_hit else "Relevant recent context"

    queue_score = 2 if worker["queue"] <= 1 else 0
    health_score = 3 if worker["health"] == "UP" else -3
    return [
        {
            "title": "Cache Warmth",
            "score": cache_score,
            "note": cache_note,
        },
        {
            "title": "Queue Length",
            "score": queue_score,
            "note": "Current load is low",
        },
        {
            "title": "Health Score",
            "score": health_score,
            "note": "Recent requests succeeded",
        },
    ]


def _build_workers_payload(snapshot):
    workers_payload = []
    for idx, w in enumerate(snapshot):
        workers_payload.append(
            {
                "id": idx,
                "label": _worker_label(idx),
                "status": _worker_status(w),
                "queue": w["queue"],
                "p95_ms": int(w["p95_ms"]),
                "errors": w["errors"],
                "cache_warmth": int(w["cache_warmth"] * 100),
            }
        )
    return workers_payload


def _build_state_payload(selected_id=0):
    snapshot = gateway.snapshot()
    worker = snapshot[selected_id] if snapshot and selected_id < len(snapshot) else None
    return {
        "backend": _STATE["backend"],
        "mode": _mode_label(_STATE["backend"]),
        "scale": _STATE["scale"],
        "scale_status": _STATE["scale_status"],
        "scale_error": _STATE["scale_error"],
        "routing_mode": _STATE["routing_mode"],
        "kill_worker": _STATE["kill_worker"],
        "delay_s": _STATE["delay_s"],
        "error_rate": _STATE["error_rate"],
        "rate_limit": _STATE["rate_limit"],
        "selected_worker": _worker_label(selected_id),
        "why": _build_why(worker),
        "workers_detail": _build_workers_payload(snapshot),
    }


def _load_latest_stress_report():
    try:
        if not os.path.isdir(_REPORTS_LOAD_DIR):
            return None
        run_ids = sorted(
            [
                run_id
                for run_id in os.listdir(_REPORTS_LOAD_DIR)
                if os.path.isdir(os.path.join(_REPORTS_LOAD_DIR, run_id))
            ],
            reverse=True,
        )
        for run_id in run_ids:
            results_path = os.path.join(_REPORTS_LOAD_DIR, run_id, "results.json")
            if not os.path.isfile(results_path):
                continue
            with open(results_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            payload["run_id"] = run_id
            payload["source_file"] = os.path.relpath(
                results_path, os.path.dirname(__file__)
            )
            return payload
    except Exception:
        return None
    return None


def _apply_state(payload):
    backend = payload.get("backend", _STATE["backend"])
    backend_value = _normalize_backend(backend)
    scale_raw = payload.get("scale", _STATE["scale"])
    routing_mode = payload.get("routing_mode", _STATE["routing_mode"])
    kill_worker = bool(payload.get("kill_worker", _STATE["kill_worker"]))
    delay_s = float(payload.get("delay_s", _STATE["delay_s"]) or 0.0)
    error_rate = float(payload.get("error_rate", _STATE["error_rate"]) or 0.0)
    rate_limit = int(
        payload.get("rate_limit", _STATE["rate_limit"]) or _DEFAULT_RATE_LIMIT
    )
    if routing_mode not in ("least_queue", "cache_aware", "round_robin"):
        routing_mode = _STATE["routing_mode"]

    try:
        requested_scale = max(1, int(scale_raw))
    except Exception:
        requested_scale = int(_STATE["scale"])

    should_rescale = (
        backend_value != _STATE["backend"] or requested_scale != int(_STATE["scale"])
    )
    if should_rescale:
        scale, scale_status, scale_error = _scale_workers(requested_scale, backend_value)
    else:
        scale = int(_STATE["scale"])
        scale_status = _STATE["scale_status"]
        scale_error = _STATE["scale_error"]

    gateway.set_worker_count(scale)
    gateway.set_chaos(delay_s, error_rate)
    gateway.apply_kill(0 if kill_worker else None)
    _set_rate_limit(rate_limit)
    _STATE.update(
        {
            "backend": backend_value,
            "scale": scale,
            "scale_status": scale_status,
            "scale_error": scale_error,
            "routing_mode": routing_mode,
            "kill_worker": kill_worker,
            "delay_s": delay_s,
            "error_rate": error_rate,
            "rate_limit": rate_limit,
        }
    )
    return backend_value, routing_mode


def _handle_request(payload):
    prompt = (payload.get("prompt") or "").strip()
    if not prompt:
        return {"error": "prompt is required"}

    backend_value, routing_mode = _apply_state(payload)

    grpc_target = os.getenv("GRPC_TARGET") or "localhost:50051"
    result = gateway.handle(
        prompt,
        backend_value,
        routing_mode,
        grpc_target=grpc_target,
    )

    status = "OK" if result["error"] is None else "ERROR"
    selected_mode = _mode_label(backend_value)
    snapshot = gateway.snapshot()
    selected_worker_label = _resolve_selected_worker(result, backend_value, _STATE["scale"])

    display_worker = 0
    if isinstance(selected_worker_label, str) and len(selected_worker_label) == 1:
        maybe_idx = ord(selected_worker_label.upper()) - ord("A")
        if 0 <= maybe_idx < len(snapshot):
            display_worker = maybe_idx

    worker = snapshot[display_worker] if snapshot and display_worker < len(snapshot) else None
    why = _build_why(worker, result.get("reason"))
    worker_identity = _extract_worker_identity_from_result(result) or None

    return {
        "text": result["text"],
        "status": status,
        "mode": selected_mode,
        "latency_ms": int(result["latency_ms"]),
        "cache_hit": result.get("cache_hit"),
        "workers": _STATE["scale"],
        "request_id": result["request_id"],
        "error": result["error"],
        "scale_status": _STATE["scale_status"],
        "scale_error": _STATE["scale_error"],
        "selected_worker": selected_worker_label,
        "worker_identity": worker_identity,
        "why": why,
        "workers_detail": _build_workers_payload(snapshot),
    }


class Handler(BaseHTTPRequestHandler):
    def _send_bytes(self, body, status=200, content_type="application/octet-stream"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self, path):
        if not _HAVE_STATIC:
            return False

        rel = unquote(path.lstrip("/"))
        if rel == "":
            rel = "index.html"
        candidate = os.path.abspath(os.path.join(_STATIC_DIR, rel))
        if not candidate.startswith(_STATIC_DIR):
            self.send_error(403)
            return True

        if os.path.isfile(candidate):
            mime, _ = mimetypes.guess_type(candidate)
            with open(candidate, "rb") as handle:
                body = handle.read()
            self._send_bytes(body, 200, mime or "application/octet-stream")
            return True

        # SPA fallback
        if os.path.isfile(_STATIC_INDEX):
            with open(_STATIC_INDEX, "rb") as handle:
                body = handle.read()
            self._send_bytes(body, 200, "text/html; charset=utf-8")
            return True

        return False

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            body = json.dumps({"ok": True}).encode("utf-8")
            self._send_bytes(body, 200, "application/json")
            return
        if path == "/api/state":
            body = json.dumps(_build_state_payload()).encode("utf-8")
            self._send_bytes(body, 200, "application/json")
            return
        if path == "/api/stress/latest":
            report = _load_latest_stress_report()
            if report is None:
                body = json.dumps({"error": "no_stress_report_found"}).encode("utf-8")
                self._send_bytes(body, 404, "application/json")
            else:
                body = json.dumps(report).encode("utf-8")
                self._send_bytes(body, 200, "application/json")
            return
        if self._serve_static(path):
            return
        self.send_error(404)

    def do_POST(self):
        path = urlparse(self.path).path
        if path not in ("/api/submit", "/api/state"):
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception:
            payload = {}

        if path == "/api/state":
            _apply_state(payload)
            data = _build_state_payload()
        else:
            data = _handle_request(payload)
        body = json.dumps(data).encode("utf-8")
        self._send_bytes(
            body,
            200 if data.get("error") is None else 400,
            "application/json",
        )

    def log_message(self, format, *args):
        return


def main():
    server = ThreadingHTTPServer((_HOST, _PORT), Handler)
    url = f"http://{_HOST}:{_PORT}"
    print(f"API: {url} (POST /api/submit)")
    server.serve_forever()


if __name__ == "__main__":
    main()
