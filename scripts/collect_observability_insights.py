#!/usr/bin/env python3
import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus
from urllib.request import urlopen


def _parse_iso(ts):
    if not ts:
        return None
    value = str(ts).strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(value)
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _query_prometheus(base_url, expr, query_time=None):
    query = quote_plus(expr)
    url = f"{base_url.rstrip('/')}/api/v1/query?query={query}"
    if query_time is not None:
        url += f"&time={quote_plus(str(query_time))}"
    with urlopen(url, timeout=5) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    if payload.get("status") != "success":
        return []
    data = payload.get("data") or {}
    result = data.get("result") or []
    return result if isinstance(result, list) else []


def _vector_to_scalar(vector):
    if not vector:
        return None
    item = vector[0] if isinstance(vector[0], dict) else {}
    value = item.get("value")
    if not isinstance(value, list) or len(value) < 2:
        return None
    try:
        parsed = float(value[1])
    except Exception:
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def _vector_to_map(vector, label_key):
    output = {}
    for row in vector:
        if not isinstance(row, dict):
            continue
        metric = row.get("metric") or {}
        label = str(metric.get(label_key) or "").strip()
        if not label:
            continue
        value = row.get("value")
        if not isinstance(value, list) or len(value) < 2:
            continue
        try:
            parsed = float(value[1])
        except Exception:
            continue
        if not math.isfinite(parsed):
            continue
        output[label] = parsed
    return output


def _safe_round(value, digits=4):
    if value is None:
        return None
    try:
        parsed = float(value)
    except Exception:
        return None
    if not math.isfinite(parsed):
        return None
    return round(parsed, digits)


def main():
    parser = argparse.ArgumentParser(
        description="Attach Prometheus-based observability insights to stress results.json"
    )
    parser.add_argument("--results-json", required=True)
    parser.add_argument("--prom-url", default="http://127.0.0.1:9090")
    parser.add_argument("--backend", default="LLMD")
    parser.add_argument("--window-seconds", type=int, default=0)
    args = parser.parse_args()

    results_path = Path(args.results_json)
    if not results_path.is_file():
        raise SystemExit(f"results file not found: {results_path}")

    with results_path.open("r", encoding="utf-8") as handle:
        result = json.load(handle)

    started_at = _parse_iso(result.get("started_at"))
    ended_at = _parse_iso(result.get("ended_at"))
    duration_sec = None
    if started_at and ended_at:
        duration_sec = max(1, int((ended_at - started_at).total_seconds()))
    if args.window_seconds > 0:
        window_seconds = args.window_seconds
    elif duration_sec is not None:
        # Match the exact run duration for cleaner run-scoped metrics.
        window_seconds = max(1, duration_sec)
    else:
        window_seconds = 120

    backend = str(args.backend or result.get("backend_mode") or "LLMD").upper()
    range_window = f"{window_seconds}s"
    query_time = ended_at.timestamp() if ended_at is not None else None

    try:
        req_total = _vector_to_scalar(
            _query_prometheus(
                args.prom_url,
                f'sum(increase(ict_api_requests_total{{backend="{backend}"}}[{range_window}]))',
                query_time=query_time,
            )
        )
        req_ok = _vector_to_scalar(
            _query_prometheus(
                args.prom_url,
                f'sum(increase(ict_api_requests_total{{backend="{backend}",result="ok"}}[{range_window}]))',
                query_time=query_time,
            )
        )
        req_err = _vector_to_scalar(
            _query_prometheus(
                args.prom_url,
                f'sum(increase(ict_api_requests_total{{backend="{backend}",result="error"}}[{range_window}]))',
                query_time=query_time,
            )
        )
        req_rps = _vector_to_scalar(
            _query_prometheus(
                args.prom_url,
                f'sum(rate(ict_api_requests_total{{backend="{backend}"}}[{range_window}]))',
                query_time=query_time,
            )
        )
        p50 = _vector_to_scalar(
            _query_prometheus(
                args.prom_url,
                (
                    'histogram_quantile(0.50, sum(rate(ict_api_request_latency_ms_bucket'
                    f'{{backend="{backend}"}}[{range_window}])) by (le))'
                ),
                query_time=query_time,
            )
        )
        p95 = _vector_to_scalar(
            _query_prometheus(
                args.prom_url,
                (
                    'histogram_quantile(0.95, sum(rate(ict_api_request_latency_ms_bucket'
                    f'{{backend="{backend}"}}[{range_window}])) by (le))'
                ),
                query_time=query_time,
            )
        )
        p99 = _vector_to_scalar(
            _query_prometheus(
                args.prom_url,
                (
                    'histogram_quantile(0.99, sum(rate(ict_api_request_latency_ms_bucket'
                    f'{{backend="{backend}"}}[{range_window}])) by (le))'
                ),
                query_time=query_time,
            )
        )
        workers = _vector_to_map(
            _query_prometheus(
                args.prom_url,
                (
                    'sum by (worker) (increase(ict_api_requests_total'
                    f'{{backend="{backend}",worker!=""}}[{range_window}]))'
                ),
                query_time=query_time,
            ),
            "worker",
        )
    except Exception as exc:
        result["observability"] = {
            "enabled": False,
            "source": "prometheus",
            "error": str(exc),
            "window_seconds": window_seconds,
        }
    else:
        worker_distribution = {}
        for label in ("A", "B", "C", "D", "E", "unknown"):
            if label in workers:
                worker_distribution[label] = int(round(workers[label]))
        insights = []
        if req_total is not None and req_total > 0:
            unknown = worker_distribution.get("unknown", 0)
            unknown_pct = max(0.0, min(100.0, (unknown / req_total) * 100.0))
            insights.append(
                f"Prometheus observed about {int(round(req_total))} requests in the analysis window."
            )
            if unknown_pct > 1:
                insights.append(
                    f"{unknown_pct:.2f}% of requests had unknown worker identity in API-level metrics."
                )
            else:
                insights.append("Worker identity coverage at API level stayed near-complete.")
        if p95 is not None:
            insights.append(f"Observed p95 latency from Prometheus histogram was about {p95:.2f} ms.")
        if req_rps is not None:
            insights.append(f"Average request rate from Prometheus was about {req_rps:.2f} req/s.")

        result["observability"] = {
            "enabled": True,
            "source": "prometheus",
            "window_seconds": window_seconds,
            "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "requests": {
                "total": _safe_round(req_total, 0),
                "ok": _safe_round(req_ok, 0),
                "error": _safe_round(req_err, 0),
                "rate_rps": _safe_round(req_rps, 4),
            },
            "latency_ms": {
                "p50": _safe_round(p50, 4),
                "p95": _safe_round(p95, 4),
                "p99": _safe_round(p99, 4),
            },
            "worker_distribution": worker_distribution,
            "insights": insights,
        }

    with results_path.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=True, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
