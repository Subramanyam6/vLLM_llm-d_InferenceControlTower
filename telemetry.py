import os

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
except Exception:  # pragma: no cover - optional dependency fallback
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"
    Counter = None
    Gauge = None
    Histogram = None
    generate_latest = None


def _enabled():
    raw = str(os.getenv("PROMETHEUS_METRICS_ENABLED", "1")).strip().lower()
    return raw in ("1", "true", "yes", "on")


if Counter is not None and _enabled():
    REQUEST_TOTAL = Counter(
        "ict_api_requests_total",
        "Total submit requests handled by the control tower API",
        ("backend", "result", "worker", "worker_identity"),
    )
    REQUEST_LATENCY_MS = Histogram(
        "ict_api_request_latency_ms",
        "Submit request end-to-end latency in milliseconds",
        ("backend", "result", "worker"),
        buckets=(1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000),
    )
    WORKER_QUEUE = Gauge(
        "ict_worker_queue_depth",
        "Worker queue depth from workers_detail payload",
        ("worker",),
    )
    WORKER_ERRORS = Gauge(
        "ict_worker_error_total",
        "Worker error counter from workers_detail payload",
        ("worker",),
    )
    WORKER_P95_MS = Gauge(
        "ict_worker_reported_p95_ms",
        "Worker reported p95 latency from workers_detail payload",
        ("worker",),
    )
    WORKER_CACHE_WARMTH = Gauge(
        "ict_worker_cache_warmth_pct",
        "Worker cache warmth percent from workers_detail payload",
        ("worker",),
    )
else:  # pragma: no cover - no-op fallback
    REQUEST_TOTAL = None
    REQUEST_LATENCY_MS = None
    WORKER_QUEUE = None
    WORKER_ERRORS = None
    WORKER_P95_MS = None
    WORKER_CACHE_WARMTH = None


def _normalize_worker(value):
    worker = str(value or "").strip().upper()
    return worker if len(worker) == 1 and "A" <= worker <= "Z" else "unknown"


def _normalize_backend(value):
    backend = str(value or "").strip().upper()
    return backend or "UNKNOWN"


def _normalize_result(error_value):
    return "error" if error_value else "ok"


def _normalize_identity(worker_identity):
    value = str(worker_identity or "").strip()
    return "known" if value else "missing"


def record_submit_metrics(backend, response_payload):
    if REQUEST_TOTAL is None:
        return

    data = response_payload or {}
    worker = _normalize_worker(data.get("selected_worker"))
    result = _normalize_result(data.get("error"))
    backend_label = _normalize_backend(backend)
    identity_state = _normalize_identity(data.get("worker_identity"))

    REQUEST_TOTAL.labels(
        backend=backend_label,
        result=result,
        worker=worker,
        worker_identity=identity_state,
    ).inc()

    latency_ms = data.get("latency_ms")
    if isinstance(latency_ms, (int, float)) and latency_ms >= 0:
        REQUEST_LATENCY_MS.labels(
            backend=backend_label,
            result=result,
            worker=worker,
        ).observe(float(latency_ms))

    workers_detail = data.get("workers_detail")
    if not isinstance(workers_detail, list):
        return

    for worker_detail in workers_detail:
        if not isinstance(worker_detail, dict):
            continue
        label = _normalize_worker(worker_detail.get("label"))
        queue = worker_detail.get("queue")
        errors = worker_detail.get("errors")
        p95_ms = worker_detail.get("p95_ms")
        cache_warmth = worker_detail.get("cache_warmth")
        if isinstance(queue, (int, float)):
            WORKER_QUEUE.labels(worker=label).set(float(queue))
        if isinstance(errors, (int, float)):
            WORKER_ERRORS.labels(worker=label).set(float(errors))
        if isinstance(p95_ms, (int, float)):
            WORKER_P95_MS.labels(worker=label).set(float(p95_ms))
        if isinstance(cache_warmth, (int, float)):
            WORKER_CACHE_WARMTH.labels(worker=label).set(float(cache_warmth))


def render_prometheus_metrics():
    if generate_latest is None:
        body = b"# Prometheus client not installed\n"
    elif not _enabled():
        body = b"# Metrics disabled (PROMETHEUS_METRICS_ENABLED=0)\n"
    else:
        body = generate_latest()
    return body, CONTENT_TYPE_LATEST
