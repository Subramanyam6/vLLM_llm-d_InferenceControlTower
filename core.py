import hashlib
import json
import os
import queue
import random
import threading
import time
import uuid
import urllib.error
import urllib.request

# Why a small token bucket: it shows rate limiting without extra deps or infrastructure.
class TokenBucket:
    def __init__(self, capacity_per_min):
        self.capacity = float(capacity_per_min)
        self.tokens = float(capacity_per_min)
        self.refill_per_sec = float(capacity_per_min) / 60.0
        self.last = time.time()
        self.lock = threading.Lock()

    def set_capacity(self, capacity_per_min):
        with self.lock:
            self.capacity = float(capacity_per_min)
            self.tokens = min(self.tokens, self.capacity)
            self.refill_per_sec = float(capacity_per_min) / 60.0

    def allow(self):
        with self.lock:
            now = time.time()
            elapsed = now - self.last
            self.last = now
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_sec)
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return True
            return False


def _fingerprint(prompt):
    # Why hash: stable cache key without storing large prompts in maps.
    return hashlib.md5(prompt.encode("utf-8")).hexdigest()[:8]


def _percentile(values, p):
    if not values:
        return 0.0
    values = sorted(values)
    k = int(round((p / 100.0) * (len(values) - 1)))
    return float(values[k])


def _fake_llm(prompt, total_delay_s):
    # Why token sleeps: it mimics streaming without needing SSE/websocket plumbing.
    tokens = (
        "Simulated answer:"
        " I understood your request"
        " and routed it through the control tower"
        " to produce a safe, fast reply."
    ).split()
    per = total_delay_s / max(1, len(tokens))
    out = []
    for t in tokens:
        time.sleep(per)
        out.append(t)
    return " ".join(out) + f" (prompt='{prompt[:48]}')"


def _env_truthy(name, default=False):
    raw = os.getenv(name)
    if raw is None:
        return bool(default)
    return str(raw).strip().lower() in ("1", "true", "yes", "on")


class Task:
    def __init__(self, prompt, fingerprint, request_id):
        self.prompt = prompt
        self.fingerprint = fingerprint
        self.request_id = request_id
        self.done = threading.Event()
        self.response = None
        self.error = None
        self.cache_hit = False
        self.worker_id = None
        self.start_ts = None
        self.end_ts = None


class Worker:
    def __init__(self, worker_id):
        self.id = worker_id
        self.q = queue.Queue()
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.healthy = True
        self.errors = 0
        self.latencies_ms = []
        self.cache = set()
        self.chaos_delay_s = 0.0
        self.error_rate = 0.0
        self.thread.start()

    def set_chaos(self, delay_s, error_rate):
        self.chaos_delay_s = float(delay_s)
        self.error_rate = float(error_rate)

    def stop(self):
        self.stop_event.set()

    def queue_len(self):
        return self.q.qsize()

    def _run(self):
        while not self.stop_event.is_set():
            try:
                task = self.q.get(timeout=0.1)
            except queue.Empty:
                continue

            if not self.healthy:
                task.error = "worker_down"
                task.done.set()
                continue

            task.start_ts = time.time()
            task.cache_hit = task.fingerprint in self.cache
            base = 0.35 if not task.cache_hit else 0.14
            jitter = random.uniform(0.02, 0.08)
            total_delay = base + jitter + self.chaos_delay_s

            if random.random() < self.error_rate:
                time.sleep(total_delay)
                task.error = "simulated_error"
                self.errors += 1
            else:
                task.response = _fake_llm(task.prompt, total_delay)
                self.cache.add(task.fingerprint)

            task.end_ts = time.time()
            task.worker_id = self.id
            self.latencies_ms.append((task.end_ts - task.start_ts) * 1000.0)
            if len(self.latencies_ms) > 200:
                self.latencies_ms = self.latencies_ms[-200:]
            task.done.set()


class Gateway:
    def __init__(
        self,
        worker_count=3,
        rate_limit_per_min=60,
        timeout_s=6.0,
        retries=1,
    ):
        self.timeout_s = float(timeout_s)
        self.retries = int(retries)
        self.bucket = TokenBucket(rate_limit_per_min)
        self.workers = []
        self.rr_index = 0
        self.chaos_delay_s = 0.0
        self.error_rate = 0.0
        self._otel_tracer = _init_tracer()
        self.set_worker_count(worker_count)

    def set_worker_count(self, n):
        n = max(1, int(n))
        if n > len(self.workers):
            for i in range(len(self.workers), n):
                self.workers.append(Worker(i))
        elif n < len(self.workers):
            for w in self.workers[n:]:
                w.stop()
            self.workers = self.workers[:n]

    def set_rate_limit(self, capacity_per_min):
        self.bucket.set_capacity(capacity_per_min)

    def set_chaos(self, delay_s, error_rate):
        self.chaos_delay_s = float(delay_s)
        self.error_rate = float(error_rate)
        for w in self.workers:
            w.set_chaos(self.chaos_delay_s, self.error_rate)

    def apply_kill(self, kill_id):
        for w in self.workers:
            w.healthy = True
        if kill_id is not None:
            for w in self.workers:
                if w.id == kill_id:
                    w.healthy = False

    def snapshot(self):
        out = []
        for w in self.workers:
            out.append(
                {
                    "id": w.id,
                    "health": "UP" if w.healthy else "DOWN",
                    "queue": w.queue_len(),
                    "p95_ms": _percentile(w.latencies_ms, 95),
                    "errors": w.errors,
                    "cache_warmth": min(1.0, len(w.cache) / 10.0),
                    "cache_size": len(w.cache),
                }
            )
        return out

    def handle(self, prompt, backend, routing_mode, grpc_target=None):
        request_id = str(uuid.uuid4())[:8]
        trace = []
        t0 = time.time()
        trace.append((t0, "received"))

        if not self.bucket.allow():
            trace.append((time.time(), "rate_limited"))
            return _result_error(request_id, "rate_limited", trace, t0)

        if backend == "GRPC":
            vllm_url = os.getenv("VLLM_HTTP_URL") or os.getenv("VLLM_OPENAI_URL")
            if vllm_url:
                return self._handle_vllm_http(prompt, request_id, trace, t0, vllm_url)
            return self._handle_grpc(prompt, request_id, trace, t0, grpc_target)
        if backend == "LLMD":
            llmd_url = (
                os.getenv("LLMD_HTTP_URL")
                or os.getenv("LLM_D_HTTP_URL")
                or os.getenv("LLMD_GATEWAY_URL")
                or "http://localhost:8000"
            )
            sglang_front_enabled = _env_truthy("ENABLE_SGLANG_FRONT", False)
            if sglang_front_enabled:
                sglang_url = os.getenv("SGLANG_HTTP_URL") or "http://127.0.0.1:30000"
                return self._handle_llmd_via_sglang(
                    prompt,
                    request_id,
                    trace,
                    t0,
                    llmd_url,
                    sglang_url,
                )
            return self._handle_llmd_http(prompt, request_id, trace, t0, llmd_url)
        if backend == "SGLANG":
            llmd_url = (
                os.getenv("LLMD_HTTP_URL")
                or os.getenv("LLM_D_HTTP_URL")
                or os.getenv("LLMD_GATEWAY_URL")
                or "http://localhost:8000"
            )
            sglang_url = os.getenv("SGLANG_HTTP_URL") or "http://127.0.0.1:30000"
            return self._handle_llmd_via_sglang(
                prompt,
                request_id,
                trace,
                t0,
                llmd_url,
                sglang_url,
            )

        return self._handle_sim(prompt, request_id, trace, t0, routing_mode)

    def _handle_sim(self, prompt, request_id, trace, t0, routing_mode):
        fp = _fingerprint(prompt)
        tried = set()
        last_error = None
        reason = {}

        for attempt in range(self.retries + 1):
            worker, reason = self._route_worker(fp, routing_mode, tried)
            if worker is None:
                last_error = "no_healthy_workers"
                break
            tried.add(worker.id)
            trace.append((time.time(), f"routed_worker_{worker.id}"))

            task = Task(prompt, fp, request_id)
            worker.q.put(task)

            ok = task.done.wait(self.timeout_s)
            if not ok:
                last_error = "timeout"
                trace.append((time.time(), "worker_timeout"))
                continue

            if task.error:
                last_error = task.error
                trace.append((time.time(), f"worker_error_{task.error}"))
                continue

            # Insert worker timestamps so the UI can render a span-like timeline.
            if task.start_ts:
                trace.append((task.start_ts, "worker_start"))
            if task.end_ts:
                trace.append((task.end_ts, "worker_end"))

            latency_ms = (time.time() - t0) * 1000.0
            trace.append((time.time(), "responded"))
            _otel_event(self._otel_tracer, "responded", {"worker": worker.id})
            return {
                "request_id": request_id,
                "text": task.response,
                "error": None,
                "worker_id": worker.id,
                "cache_hit": task.cache_hit,
                "latency_ms": latency_ms,
                "trace": trace,
                "reason": reason,
            }

        return _result_error(request_id, last_error or "unknown", trace, t0, reason)

    def _route_worker(self, fingerprint, routing_mode, tried):
        candidates = [w for w in self.workers if w.healthy and w.id not in tried]
        if not candidates:
            return None, {}

        def score(w):
            cache_hit = fingerprint in w.cache
            queue_len = w.queue_len()
            est_ms = 250.0 * (0.4 if cache_hit else 1.0) + queue_len * 80.0
            return est_ms, cache_hit, queue_len

        def pick_with_round_robin(pool):
            idx = self.rr_index % len(pool)
            self.rr_index += 1
            return pool[idx]

        if routing_mode == "round_robin":
            w = pick_with_round_robin(candidates)
            est_ms, cache_hit, queue_len = score(w)
        elif routing_mode == "least_queue":
            min_queue = min(w.queue_len() for w in candidates)
            tied = [w for w in candidates if w.queue_len() == min_queue]
            w = pick_with_round_robin(tied)
            est_ms, cache_hit, queue_len = score(w)
        else:  # cache_aware
            scored = [(w, *score(w)) for w in candidates]
            min_est = min(s[1] for s in scored)
            tied = [s[0] for s in scored if s[1] == min_est]
            w = pick_with_round_robin(tied)
            est_ms, cache_hit, queue_len = score(w)

        reason = {
            "queue_len": queue_len,
            "cache_hit": int(cache_hit),
            "est_ms": int(est_ms),
            "mode": routing_mode,
        }
        _otel_event(self._otel_tracer, "routed", {"worker": w.id, "mode": routing_mode})
        return w, reason

    def _handle_grpc(self, prompt, request_id, trace, t0, grpc_target):
        target = grpc_target or os.getenv("GRPC_TARGET") or "localhost:50051"
        model_name = (
            os.getenv("MODEL_NAME")
            or os.getenv("LLMD_MODEL")
            or os.getenv("MODEL")
            or "fake-model"
        )
        payload = {
            "model": model_name,
            "prompt": prompt,
            "max_tokens": 128,
            "temperature": 0.2,
        }
        trace.append((time.time(), "grpc_request"))
        _otel_event(self._otel_tracer, "grpc_request", {"target": target})

        try:
            import grpc
        except Exception as e:
            return _result_error(
                request_id,
                f"grpc_unavailable: {e}",
                trace,
                t0,
                {"mode": "grpc", "target": target},
            )

        try:
            with grpc.insecure_channel(target) as channel:
                method = channel.unary_unary(
                    "/inference.InferenceService/Generate",
                    request_serializer=lambda data: json.dumps(data).encode("utf-8"),
                    response_deserializer=lambda data: json.loads(data.decode("utf-8")),
                )
                data = method(payload, timeout=self.timeout_s)
            text = _parse_grpc_response(data)
            worker_identity = _extract_worker_identity(data)
            latency_ms = (time.time() - t0) * 1000.0
            trace.append((time.time(), "responded"))
            reason = {"mode": "grpc", "target": target}
            if worker_identity:
                reason["worker_identity"] = worker_identity
            return {
                "request_id": request_id,
                "text": text,
                "error": None,
                "worker_id": worker_identity or "grpc",
                "cache_hit": None,
                "latency_ms": latency_ms,
                "trace": trace,
                "reason": reason,
            }
        except Exception as e:
            trace.append((time.time(), "grpc_error"))
            return _result_error(
                request_id,
                f"grpc_error: {e}",
                trace,
                t0,
                {"mode": "grpc", "target": target},
            )

    def _handle_vllm_http(self, prompt, request_id, trace, t0, base_url):
        model_name = (
            os.getenv("MODEL_NAME")
            or os.getenv("LLMD_MODEL")
            or os.getenv("MODEL")
            or "fake-model"
        )
        url = base_url.rstrip("/") + "/v1/completions"
        payload = {
            "model": model_name,
            "prompt": prompt,
            "max_tokens": 128,
            "temperature": 0.2,
        }
        trace.append((time.time(), "vllm_http_request"))
        _otel_event(self._otel_tracer, "vllm_http_request", {"url": url})

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                data = resp.read().decode("utf-8")
                header_obj = getattr(resp, "headers", None)
                headers = {k: v for k, v in header_obj.items()} if hasattr(header_obj, "items") else {}
            parsed = json.loads(data)
            text = _parse_openai_response(parsed)
            worker_identity = _extract_worker_identity(parsed, headers)
            latency_ms = (time.time() - t0) * 1000.0
            trace.append((time.time(), "responded"))
            reason = {"mode": "vllm_http", "url": url}
            if worker_identity:
                reason["worker_identity"] = worker_identity
            return {
                "request_id": request_id,
                "text": text,
                "error": None,
                "worker_id": worker_identity or "vllm",
                "cache_hit": None,
                "latency_ms": latency_ms,
                "trace": trace,
                "reason": reason,
            }
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8")
            except Exception:
                body = ""
            trace.append((time.time(), "vllm_http_error"))
            return _result_error(
                request_id,
                f"vllm_http_error: {e.code} {body}".strip(),
                trace,
                t0,
                {"mode": "vllm_http", "url": url},
            )
        except Exception as e:
            trace.append((time.time(), "vllm_http_error"))
            return _result_error(
                request_id,
                f"vllm_http_error: {e}",
                trace,
                t0,
                {"mode": "vllm_http", "url": url},
            )

    def _rewrite_prompt_with_sglang(self, prompt, request_id, trace, t0, sglang_url):
        model_name = (
            os.getenv("MODEL_NAME")
            or os.getenv("SGLANG_MODEL")
            or os.getenv("MODEL")
            or "default"
        )
        base_url = sglang_url.rstrip("/")
        if "/v1/" in base_url:
            url = base_url
        else:
            url = base_url + "/v1/chat/completions"

        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Rewrite the user prompt into a concise, clear instruction for downstream inference. "
                        "Preserve intent, entities, constraints, and safety context. "
                        "Return only the rewritten prompt text."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 256,
            "temperature": 0.0,
        }
        trace.append((time.time(), "sglang_front_request"))
        _otel_event(self._otel_tracer, "sglang_front_request", {"url": url})

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                data = resp.read().decode("utf-8")
                header_obj = getattr(resp, "headers", None)
                headers = {k: v for k, v in header_obj.items()} if hasattr(header_obj, "items") else {}
            parsed = json.loads(data)
            rewritten_prompt = _parse_openai_response(parsed).strip() or prompt
            worker_identity = _extract_worker_identity(parsed, headers)
            trace.append((time.time(), "sglang_front_responded"))
            return {
                "prompt": rewritten_prompt,
                "worker_identity": worker_identity,
                "error": None,
                "url": url,
            }
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8")
            except Exception:
                body = ""
            trace.append((time.time(), "sglang_front_error"))
            return {
                "prompt": prompt,
                "worker_identity": "",
                "error": f"sglang_front_error: {e.code} {body}".strip(),
                "url": url,
            }
        except Exception as e:
            trace.append((time.time(), "sglang_front_error"))
            return {
                "prompt": prompt,
                "worker_identity": "",
                "error": f"sglang_front_error: {e}",
                "url": url,
            }

    def _handle_llmd_via_sglang(
        self,
        prompt,
        request_id,
        trace,
        t0,
        llmd_url,
        sglang_url,
    ):
        rewritten = self._rewrite_prompt_with_sglang(
            prompt,
            request_id,
            trace,
            t0,
            sglang_url,
        )
        if rewritten.get("error"):
            return _result_error(
                request_id,
                rewritten["error"],
                trace,
                t0,
                {
                    "mode": "llm-d+sglang",
                    "llmd_url": llmd_url,
                    "sglang_url": rewritten.get("url") or sglang_url,
                },
            )

        llmd_result = self._handle_llmd_http(
            rewritten["prompt"],
            request_id,
            trace,
            t0,
            llmd_url,
        )
        reason = llmd_result.get("reason") or {}
        reason.update(
            {
                "mode": "llm-d+sglang",
                "llmd_url": llmd_url,
                "sglang_url": rewritten.get("url") or sglang_url,
            }
        )
        if rewritten["prompt"] != prompt:
            reason["sglang_rewrote_prompt"] = 1
        if rewritten.get("worker_identity"):
            reason["sglang_identity"] = rewritten["worker_identity"]
        if llmd_result.get("error") is None and _looks_generic_identity(
            llmd_result.get("worker_id")
        ):
            if rewritten.get("worker_identity"):
                llmd_result["worker_id"] = rewritten["worker_identity"]
        llmd_result["reason"] = reason
        return llmd_result

    def _handle_llmd_http(self, prompt, request_id, trace, t0, base_url):
        model_name = (
            os.getenv("MODEL_NAME")
            or os.getenv("LLMD_MODEL")
            or os.getenv("MODEL")
            or "fake-model"
        )
        base_url = base_url.rstrip("/")
        if "/v1/" in base_url:
            url = base_url
        else:
            url = base_url + "/v1/chat/completions"
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 128,
            "temperature": 0.2,
        }
        trace.append((time.time(), "llmd_http_request"))
        _otel_event(self._otel_tracer, "llmd_http_request", {"url": url})

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                data = resp.read().decode("utf-8")
                header_obj = getattr(resp, "headers", None)
                headers = {k: v for k, v in header_obj.items()} if hasattr(header_obj, "items") else {}
            parsed = json.loads(data)
            text = _parse_openai_response(parsed)
            worker_identity = _extract_worker_identity(parsed, headers)
            latency_ms = (time.time() - t0) * 1000.0
            trace.append((time.time(), "responded"))
            reason = {"mode": "llm-d", "url": url}
            if worker_identity:
                reason["worker_identity"] = worker_identity
            return {
                "request_id": request_id,
                "text": text,
                "error": None,
                "worker_id": worker_identity or "llm-d",
                "cache_hit": None,
                "latency_ms": latency_ms,
                "trace": trace,
                "reason": reason,
            }
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8")
            except Exception:
                body = ""
            trace.append((time.time(), "llmd_http_error"))
            return _result_error(
                request_id,
                f"llmd_http_error: {e.code} {body}".strip(),
                trace,
                t0,
                {"mode": "llm-d", "url": url},
            )
        except Exception as e:
            trace.append((time.time(), "llmd_http_error"))
            return _result_error(
                request_id,
                f"llmd_http_error: {e}",
                trace,
                t0,
                {"mode": "llm-d", "url": url},
            )

    def _handle_sglang_http(self, prompt, request_id, trace, t0, base_url):
        model_name = (
            os.getenv("MODEL_NAME")
            or os.getenv("SGLANG_MODEL")
            or os.getenv("MODEL")
            or "default"
        )
        base_url = base_url.rstrip("/")
        if "/v1/" in base_url:
            url = base_url
        else:
            url = base_url + "/v1/chat/completions"
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 128,
            "temperature": 0.2,
        }
        trace.append((time.time(), "sglang_http_request"))
        _otel_event(self._otel_tracer, "sglang_http_request", {"url": url})

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                data = resp.read().decode("utf-8")
                header_obj = getattr(resp, "headers", None)
                headers = {k: v for k, v in header_obj.items()} if hasattr(header_obj, "items") else {}
            parsed = json.loads(data)
            text = _parse_openai_response(parsed)
            worker_identity = _extract_worker_identity(parsed, headers)
            latency_ms = (time.time() - t0) * 1000.0
            trace.append((time.time(), "responded"))
            reason = {"mode": "sglang", "url": url}
            if worker_identity:
                reason["worker_identity"] = worker_identity
            return {
                "request_id": request_id,
                "text": text,
                "error": None,
                "worker_id": worker_identity or "sglang",
                "cache_hit": None,
                "latency_ms": latency_ms,
                "trace": trace,
                "reason": reason,
            }
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8")
            except Exception:
                body = ""
            trace.append((time.time(), "sglang_http_error"))
            return _result_error(
                request_id,
                f"sglang_http_error: {e.code} {body}".strip(),
                trace,
                t0,
                {"mode": "sglang", "url": url},
            )
        except Exception as e:
            trace.append((time.time(), "sglang_http_error"))
            return _result_error(
                request_id,
                f"sglang_http_error: {e}",
                trace,
                t0,
                {"mode": "sglang", "url": url},
            )

def _parse_grpc_response(data):
    if isinstance(data, dict):
        for key in ("text", "response", "output"):
            if data.get(key):
                return str(data[key])
    return str(data)


def _extract_worker_identity(data=None, headers=None):
    candidates = []
    if isinstance(data, dict):
        for key in (
            "worker_identity",
            "worker_id",
            "worker",
            "worker_name",
            "pod",
            "pod_name",
            "hostname",
            "instance",
            "replica",
            "served_by",
            "backend_id",
        ):
            value = data.get(key)
            if value:
                candidates.append(value)

    if headers:
        normalized = {str(k).lower(): v for k, v in headers.items()}
        for key in (
            "x-worker-identity",
            "x-worker-id",
            "x-worker",
            "x-pod-name",
            "x-pod",
            "x-hostname",
            "x-instance-id",
            "x-served-by",
            "x-upstream-host",
        ):
            value = normalized.get(key)
            if value:
                candidates.append(value)

    for candidate in candidates:
        value = str(candidate).strip()
        if not value:
            continue
        # Header can contain comma-separated values; prefer first concrete token.
        if "," in value:
            value = value.split(",", 1)[0].strip()
        if value:
            return value[:120]
    return ""


def _looks_generic_identity(worker_id):
    if worker_id is None:
        return True
    value = str(worker_id).strip().lower()
    if not value:
        return True
    return value in {"grpc", "llm-d", "sglang", "vllm", "vllm_http"}


def _parse_openai_response(data):
    if not isinstance(data, dict):
        return str(data)
    choices = data.get("choices") or []
    if not choices:
        return str(data)
    first = choices[0] or {}
    if "text" in first and first["text"] is not None:
        return str(first["text"])
    message = first.get("message") or {}
    if message.get("content"):
        return str(message["content"])
    return str(data)


def _result_error(request_id, error, trace, t0, reason=None):
    trace.append((time.time(), "responded"))
    return {
        "request_id": request_id,
        "text": f"ERROR: {error}",
        "error": error,
        "worker_id": None,
        "cache_hit": None,
        "latency_ms": (time.time() - t0) * 1000.0,
        "trace": trace,
        "reason": reason or {},
    }


def format_trace(trace):
    if not trace:
        return "(no trace)"
    base = min(t for t, _ in trace)
    lines = []
    for ts, label in sorted(trace, key=lambda x: x[0]):
        lines.append(f"{int((ts - base) * 1000)}ms  {label}")
    return "\n".join(lines)


def format_worker_cards(snapshot):
    if not snapshot:
        return "(no workers)"
    blocks = []
    for w in snapshot:
        blocks.append(
            "\n".join(
                [
                    f"**Worker-{w['id']}**",
                    f"- health: {w['health']}",
                    f"- queue: {w['queue']}",
                    f"- p95: {int(w['p95_ms'])}ms",
                    f"- errors: {w['errors']}",
                    f"- cache warmth: {int(w['cache_warmth'] * 100)}%",
                ]
            )
        )
    return "\n\n".join(blocks)


def format_flight_path(worker_id, reason):
    wid = worker_id if worker_id is not None else "?"
    lines = ["**Flight Path**", f"User -> Gateway -> Worker-{wid}", "", "**Why This Worker?**"]
    if reason:
        if "queue_len" in reason:
            lines.append(f"- queue_len: {reason['queue_len']}")
        if "cache_hit" in reason:
            lines.append(f"- cache_hit: {reason['cache_hit']}")
        if "est_ms" in reason:
            lines.append(f"- est_ms: {reason['est_ms']}ms")
    return "\n".join(lines)


def _init_tracer():
    if os.getenv("OTEL") != "1":
        return None
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        trace.set_tracer_provider(provider)
        return trace.get_tracer("inference-control-tower")
    except Exception:
        return None


def _otel_event(tracer, name, attrs=None):
    if tracer is None:
        return
    try:
        span = tracer.start_span(name)
        if attrs:
            for k, v in attrs.items():
                span.set_attribute(k, v)
        span.end()
    except Exception:
        pass
