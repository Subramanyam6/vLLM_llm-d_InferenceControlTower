#!/usr/bin/env python3
import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _read_summary(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _metric_value(metrics, metric_name, value_name, default=0.0):
    metric = metrics.get(metric_name)
    if not isinstance(metric, dict):
        return default
    values = metric.get("values")
    if not isinstance(values, dict):
        values = metric
    value = values.get(value_name, default)
    if value is None:
        return default
    try:
        return float(value)
    except Exception:
        if default is None:
            return None
        return float(default)


def _metric_count(metrics, metric_name, default=0):
    return int(round(_metric_value(metrics, metric_name, "count", default)))


def _metric_stats(metrics, metric_name, fallback_count=0):
    metric = metrics.get(metric_name)
    if not isinstance(metric, dict):
        return {"count": 0, "avg": None, "p95": None, "max": None}
    values = metric.get("values")
    if not isinstance(values, dict):
        values = metric

    def _pick(name, fallback=None):
        raw = values.get(name, fallback)
        if raw is None:
            return None
        try:
            return float(raw)
        except Exception:
            return None

    avg = _pick("avg")
    p95 = _pick("p(95)", _pick("p95"))
    max_value = _pick("max")
    count = int(round(float(values.get("count", 0) or 0)))
    has_signal = any(value is not None for value in (avg, p95, max_value))
    if count <= 0 and has_signal and fallback_count > 0:
        count = int(fallback_count)
    if count <= 0 and not has_signal:
        return {"count": 0, "avg": None, "p95": None, "max": None}
    return {"count": count, "avg": avg, "p95": p95, "max": max_value}


def _round_or_none(value, digits=3):
    if value is None:
        return None
    try:
        return round(float(value), digits)
    except Exception:
        return None


def _collect_failure_reasons(metrics):
    reasons = []
    for name, metric in metrics.items():
        if not name.startswith("failure_reason_"):
            continue
        if not isinstance(metric, dict):
            continue
        values = metric.get("values")
        if not isinstance(values, dict):
            values = metric
        count = int(round(float(values.get("count", 0) or 0)))
        if count <= 0:
            continue
        label = name.replace("failure_reason_", "").replace("_", " ")
        reasons.append({"reason": label, "count": count})
    reasons.sort(key=lambda item: item["count"], reverse=True)
    return reasons


def _collect_worker_distribution(metrics):
    labels = ("A", "B", "C", "D", "E")
    distribution = {}
    for label in labels:
        metric_name = f"worker_selected_{label.lower()}"
        distribution[label] = _metric_count(metrics, metric_name, 0)

    distribution_meta = {
        "other": _metric_count(metrics, "worker_selected_other", 0),
        "missing": _metric_count(metrics, "worker_selected_missing", 0),
    }
    distribution_meta["counted"] = sum(distribution.values()) + distribution_meta["other"] + distribution_meta["missing"]
    return distribution, distribution_meta


def _collect_worker_stats(metrics, distribution):
    worker_stats = {}
    for label in ("A", "B", "C", "D", "E"):
        suffix = label.lower()
        selected_count = int(distribution.get(label, 0))
        latency_stats = _metric_stats(
            metrics, f"worker_latency_{suffix}", fallback_count=selected_count
        )
        queue_stats = _metric_stats(
            metrics, f"worker_queue_{suffix}", fallback_count=selected_count
        )
        reported_errors_stats = _metric_stats(
            metrics, f"worker_reported_errors_{suffix}", fallback_count=selected_count
        )
        reported_p95_stats = _metric_stats(
            metrics, f"worker_reported_p95_ms_{suffix}", fallback_count=selected_count
        )
        cache_warmth_stats = _metric_stats(
            metrics, f"worker_cache_warmth_{suffix}", fallback_count=selected_count
        )

        cache_hit = _metric_count(metrics, f"worker_cache_hit_{suffix}", 0)
        cache_miss = _metric_count(metrics, f"worker_cache_miss_{suffix}", 0)
        cache_unknown = _metric_count(metrics, f"worker_cache_unknown_{suffix}", 0)
        response_error = _metric_count(metrics, f"worker_response_error_{suffix}", 0)
        cache_known_total = cache_hit + cache_miss
        cache_hit_rate = (cache_hit / cache_known_total) if cache_known_total > 0 else None

        worker_stats[label] = {
            "requests": selected_count,
            "latency_ms": {
                "count": latency_stats["count"],
                "avg": _round_or_none(latency_stats["avg"]),
                "p95": _round_or_none(latency_stats["p95"]),
                "max": _round_or_none(latency_stats["max"]),
            },
            "cache": {
                "hit": cache_hit,
                "miss": cache_miss,
                "unknown": cache_unknown,
                "hit_rate": _round_or_none(cache_hit_rate, 6),
            },
            "response_error_count": response_error,
            "observed": {
                "queue_avg": _round_or_none(queue_stats["avg"]),
                "queue_p95": _round_or_none(queue_stats["p95"]),
                "reported_errors_avg": _round_or_none(reported_errors_stats["avg"]),
                "reported_errors_max": _round_or_none(reported_errors_stats["max"]),
                "reported_p95_ms_avg": _round_or_none(reported_p95_stats["avg"]),
                "reported_p95_ms_p95": _round_or_none(reported_p95_stats["p95"]),
                "cache_warmth_avg": _round_or_none(cache_warmth_stats["avg"]),
                "cache_warmth_p95": _round_or_none(cache_warmth_stats["p95"]),
            },
        }
    return worker_stats


def _safe_iso_delta_seconds(started_at: str, ended_at: str):
    try:
        start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        end = datetime.fromisoformat(ended_at.replace("Z", "+00:00"))
        return max(0.0, (end - start).total_seconds())
    except Exception:
        return 0.0


def _parse_iso_datetime(value: str):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _percentile(values, p):
    if not values:
        return None
    values = sorted(values)
    idx = int(round((p / 100.0) * (len(values) - 1)))
    idx = max(0, min(len(values) - 1, idx))
    return float(values[idx])


def _load_llmd_pod_ip_map(path: Path):
    if not path or not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    items = payload.get("items") or []
    mapping = {}
    for item in items:
        status = item.get("status") or {}
        metadata = item.get("metadata") or {}
        ip = str(status.get("podIP") or "").strip()
        name = str(metadata.get("name") or "").strip()
        if ip and name:
            mapping[ip] = name
    return mapping


def _parse_gateway_log_line(line):
    if not line:
        return None
    line = line.strip()
    if not line.startswith("["):
        return None
    closing = line.find("]")
    if closing <= 1:
        return None
    timestamp = line[1:closing]
    if "/v1/chat/completions" not in line:
        return None

    status_match = re.search(r'"\s+(\d{3})\s', line)
    if not status_match:
        return None
    try:
        status_code = int(status_match.group(1))
    except Exception:
        return None

    # Envoy access log has four numeric fields before x-forwarded-for.
    metrics_match = re.search(
        r'"\s+\d{3}\s+.*?\s(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+"', line
    )
    duration_ms = None
    if metrics_match:
        try:
            duration_ms = float(metrics_match.group(3))
        except Exception:
            duration_ms = None

    quoted_parts = re.findall(r'"([^"]*)"', line)
    if len(quoted_parts) < 2:
        return None
    request_line = quoted_parts[0]
    upstream_host = quoted_parts[-1]
    upstream_ip = str(upstream_host).split(":", 1)[0].strip()
    if not upstream_ip:
        return None
    return {
        "timestamp": timestamp,
        "request_line": request_line,
        "status_code": status_code,
        "duration_ms": duration_ms,
        "upstream_ip": upstream_ip,
        "upstream_host": upstream_host,
    }


def _aggregate_llmd_gateway_logs(log_path: Path, pod_ip_map, started_at: str, ended_at: str):
    if not log_path or not log_path.exists():
        return None
    start_dt = _parse_iso_datetime(started_at)
    end_dt = _parse_iso_datetime(ended_at)
    if start_dt is None or end_dt is None:
        return None
    # Shell timestamps are second-granularity; add a small grace window.
    start_window = start_dt - timedelta(seconds=1)
    end_window = end_dt + timedelta(seconds=1)

    by_pod = {}
    unmatched_ip_counts = {}
    parsed_rows = 0

    with log_path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            parsed = _parse_gateway_log_line(raw_line)
            if not parsed:
                continue
            row_dt = _parse_iso_datetime(parsed["timestamp"])
            if row_dt is None:
                continue
            if row_dt < start_window or row_dt > end_window:
                continue

            parsed_rows += 1
            pod_name = pod_ip_map.get(parsed["upstream_ip"])
            if not pod_name:
                unmatched_ip_counts[parsed["upstream_ip"]] = (
                    unmatched_ip_counts.get(parsed["upstream_ip"], 0) + 1
                )
                continue

            pod_stats = by_pod.setdefault(
                pod_name,
                {
                    "requests": 0,
                    "error_count": 0,
                    "durations_ms": [],
                    "upstream_ip": parsed["upstream_ip"],
                },
            )
            pod_stats["requests"] += 1
            if parsed["status_code"] >= 400:
                pod_stats["error_count"] += 1
            if parsed["duration_ms"] is not None:
                pod_stats["durations_ms"].append(float(parsed["duration_ms"]))

    if parsed_rows <= 0:
        return None

    ordered_pods = sorted(by_pod.keys())
    selected_pods = ordered_pods[:5]
    overflow_pods = ordered_pods[5:]
    overflow_count = sum(by_pod[pod]["requests"] for pod in overflow_pods)
    missing_count = sum(unmatched_ip_counts.values())

    labels = ("A", "B", "C", "D", "E")
    distribution = {label: 0 for label in labels}
    worker_stats = {label: None for label in labels}
    pod_map_by_label = {}
    pod_ip_by_label = {}

    for idx, pod_name in enumerate(selected_pods):
        label = labels[idx]
        pod_stats = by_pod[pod_name]
        durations = pod_stats.get("durations_ms") or []
        latency_avg = sum(durations) / len(durations) if durations else None
        distribution[label] = int(pod_stats["requests"])
        worker_stats[label] = {
            "requests": int(pod_stats["requests"]),
            "latency_avg_ms": _round_or_none(latency_avg),
            "latency_p95_ms": _round_or_none(_percentile(durations, 95)),
            "latency_max_ms": _round_or_none(max(durations) if durations else None),
            "response_error_count": int(pod_stats["error_count"]),
        }
        pod_map_by_label[label] = pod_name
        pod_ip_by_label[label] = pod_stats.get("upstream_ip")

    return {
        "distribution": distribution,
        "worker_stats": worker_stats,
        "pod_map": pod_map_by_label,
        "pod_ip_map": pod_ip_by_label,
        "meta": {
            "other": int(overflow_count),
            "missing": int(missing_count),
            "counted": int(parsed_rows),
            "matched": int(parsed_rows - missing_count),
        },
    }


def _merge_gateway_distribution(
    result,
    worker_distribution,
    worker_distribution_meta,
    worker_stats,
    gateway_distribution,
):
    if not gateway_distribution:
        result["worker_distribution_source"] = "submit_response"
        result["worker_pod_map"] = {}
        result["worker_pod_ip_map"] = {}
        return worker_distribution, worker_distribution_meta, worker_stats

    merged_distribution = dict(worker_distribution)
    merged_distribution.update(gateway_distribution["distribution"])

    merged_meta = {
        "other": int(gateway_distribution["meta"]["other"]),
        "missing": int(gateway_distribution["meta"]["missing"]),
        "counted": int(gateway_distribution["meta"]["counted"]),
        "matched": int(gateway_distribution["meta"]["matched"]),
    }

    merged_worker_stats = dict(worker_stats)
    for label in ("A", "B", "C", "D", "E"):
        existing = dict(merged_worker_stats.get(label) or {})
        gateway_worker = gateway_distribution["worker_stats"].get(label)
        if gateway_worker:
            latency = dict(existing.get("latency_ms") or {})
            latency["count"] = int(gateway_worker["requests"])
            latency["avg"] = gateway_worker["latency_avg_ms"]
            latency["p95"] = gateway_worker["latency_p95_ms"]
            latency["max"] = gateway_worker["latency_max_ms"]
            existing["latency_ms"] = latency
            existing["requests"] = int(gateway_worker["requests"])
            existing["response_error_count"] = int(gateway_worker["response_error_count"])
        merged_worker_stats[label] = existing

    result["worker_distribution_source"] = "llmd_gateway_logs"
    result["worker_pod_map"] = gateway_distribution["pod_map"]
    result["worker_pod_ip_map"] = gateway_distribution["pod_ip_map"]
    return merged_distribution, merged_meta, merged_worker_stats


def _build_markdown(result, failure_reasons, slo):
    status = "PASS" if result["slo_pass"] else "FAIL"
    lines = []
    lines.append("# Stress Test Summary")
    lines.append("")
    lines.append("## Run Metadata")
    lines.append("")
    lines.append(f"- Profile: `{result['profile']}`")
    lines.append(f"- Backend: `{result['backend_mode']}`")
    lines.append(f"- Target URL: `{result['target_url']}`")
    lines.append(f"- Started: `{result['started_at']}`")
    lines.append(f"- Ended: `{result['ended_at']}`")
    lines.append(f"- Target Requests: `{result['target_requests']}`")
    lines.append("")
    lines.append("## Key Metrics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Requests attempted | {result['requests_attempted']} |")
    lines.append(f"| Requests succeeded | {result['requests_succeeded']} |")
    lines.append(f"| Requests failed | {result['requests_failed']} |")
    lines.append(f"| Error rate | {result['error_rate']:.4f} |")
    lines.append(f"| Throughput (req/s) | {result['throughput_rps']:.2f} |")
    lines.append(f"| p50 latency (ms) | {result['latency_ms']['p50']:.2f} |")
    lines.append(f"| p95 latency (ms) | {result['latency_ms']['p95']:.2f} |")
    lines.append(f"| p99 latency (ms) | {result['latency_ms']['p99']:.2f} |")
    lines.append("")
    lines.append("## Worker Distribution (A-E)")
    lines.append("")
    lines.append(
        f"- Source: `{result.get('worker_distribution_source', 'submit_response')}`"
    )
    pod_map = result.get("worker_pod_map") or {}
    pod_ip_map = result.get("worker_pod_ip_map") or {}
    if pod_map:
        lines.append("- Worker label mapping:")
        for label in ("A", "B", "C", "D", "E"):
            pod_name = pod_map.get(label)
            if not pod_name:
                continue
            pod_ip = pod_ip_map.get(label)
            if pod_ip:
                lines.append(f"  - {label} -> `{pod_name}` ({pod_ip})")
            else:
                lines.append(f"  - {label} -> `{pod_name}`")
    lines.append("")
    lines.append("| Worker | Requests | Share |")
    lines.append("| --- | --- | --- |")
    for label in ("A", "B", "C", "D", "E"):
        count = int(result["worker_distribution"].get(label, 0))
        share = float(result["worker_distribution_pct"].get(label, 0.0))
        lines.append(f"| {label} | {count} | {share:.2f}% |")
    lines.append("")
    lines.append(
        f"- Raw extras: other={result['worker_distribution_meta']['other']}, "
        f"missing={result['worker_distribution_meta']['missing']}, "
        f"counted={result['worker_distribution_meta']['counted']}"
    )
    lines.append("")
    lines.append("## Worker Detail Signals (A-E)")
    lines.append("")
    lines.append(
        "| Worker | Avg latency (ms) | p95 latency (ms) | Cache hit rate | "
        "Queue avg | Reported errors avg | Reported p95 avg (ms) | Cache warmth avg | API errors |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for label in ("A", "B", "C", "D", "E"):
        stats = result["worker_stats"].get(label, {})
        latency = stats.get("latency_ms", {})
        cache = stats.get("cache", {})
        observed = stats.get("observed", {})
        hit_rate = cache.get("hit_rate")
        hit_rate_text = f"{float(hit_rate) * 100.0:.2f}%" if hit_rate is not None else "n/a"
        latency_avg = latency.get("avg")
        latency_p95 = latency.get("p95")
        queue_avg = observed.get("queue_avg")
        err_avg = observed.get("reported_errors_avg")
        reported_p95_avg = observed.get("reported_p95_ms_avg")
        cache_warmth_avg = observed.get("cache_warmth_avg")
        lines.append(
            f"| {label} | "
            f"{latency_avg if latency_avg is not None else 'n/a'} | "
            f"{latency_p95 if latency_p95 is not None else 'n/a'} | "
            f"{hit_rate_text} | "
            f"{queue_avg if queue_avg is not None else 'n/a'} | "
            f"{err_avg if err_avg is not None else 'n/a'} | "
            f"{reported_p95_avg if reported_p95_avg is not None else 'n/a'} | "
            f"{cache_warmth_avg if cache_warmth_avg is not None else 'n/a'} | "
            f"{int(stats.get('response_error_count') or 0)} |"
        )
    lines.append("")
    lines.append("## Worker Identity Coverage")
    lines.append("")
    lines.append(f"- identity known: {result['worker_identity']['known']}")
    lines.append(f"- identity missing: {result['worker_identity']['missing']}")
    lines.append(f"- identity generic: {result['worker_identity']['generic']}")
    lines.append(
        f"- identity coverage: {result['worker_identity']['coverage_pct']:.2f}%"
    )
    lines.append("")
    lines.append("## Pass/Fail")
    lines.append("")
    lines.append(f"- Result: **{status}**")
    lines.append(f"- SLO p95 <= {slo['p95_ms']} ms")
    lines.append(f"- SLO error_rate <= {slo['error_rate_max']}")
    lines.append("")
    lines.append("## Top Failure Reasons")
    lines.append("")
    if failure_reasons:
        for item in failure_reasons[:5]:
            lines.append(f"- {item['reason']}: {item['count']}")
    else:
        lines.append("- No failures recorded.")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Render stress report from k6 summary JSON")
    parser.add_argument("--summary", required=True, help="Path to k6 summary JSON")
    parser.add_argument("--profile", required=True, help="Profile name")
    parser.add_argument("--target-requests", required=True, type=int)
    parser.add_argument("--backend", required=True, help="Backend mode")
    parser.add_argument("--target", required=True, help="Target URL")
    parser.add_argument("--output-json", required=True, help="Output path for results.json")
    parser.add_argument("--output-md", required=True, help="Output path for summary.md")
    parser.add_argument("--started-at", required=False)
    parser.add_argument("--ended-at", required=False)
    parser.add_argument("--slo-p95-ms", type=float, default=2000.0)
    parser.add_argument("--slo-error-rate-max", type=float, default=0.02)
    parser.add_argument("--gateway-log", required=False, help="Path to llm-d gateway access logs")
    parser.add_argument("--llmd-pods-json", required=False, help="Path to llm-d decode pods JSON")
    args = parser.parse_args()

    summary_path = Path(args.summary)
    data = _read_summary(summary_path)
    metrics = data.get("metrics") or {}

    attempted = _metric_count(metrics, "http_reqs", 0)
    successful = _metric_count(metrics, "successful_requests", 0)
    failed = _metric_count(metrics, "failed_requests", 0)

    if successful == 0 and failed == 0 and attempted > 0:
        failed_rate_fallback = _metric_value(metrics, "http_req_failed", "value", None)
        if failed_rate_fallback is None:
            failed_rate_fallback = _metric_value(metrics, "http_req_failed", "rate", 0.0)
        failed = int(round(attempted * failed_rate_fallback))
        successful = max(0, attempted - failed)

    if attempted == 0:
        attempted = successful + failed

    if attempted > 0 and successful == 0 and failed > 0:
        successful = max(0, attempted - failed)

    error_rate = (failed / attempted) if attempted > 0 else 0.0
    throughput = _metric_value(metrics, "http_reqs", "rate", 0.0)

    p50 = _metric_value(metrics, "http_req_duration", "p(50)", None)
    if p50 is None or p50 == 0:
        p50 = _metric_value(metrics, "http_req_duration", "med", 0.0)
    p95 = _metric_value(metrics, "http_req_duration", "p(95)", 0.0)
    p99 = _metric_value(metrics, "http_req_duration", "p(99)", None)
    if p99 is None or p99 == 0:
        p99 = _metric_value(metrics, "http_req_duration", "max", 0.0)

    started_at = args.started_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ended_at = args.ended_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    duration_s = _safe_iso_delta_seconds(started_at, ended_at)
    if duration_s > 0 and throughput == 0 and attempted > 0:
        throughput = attempted / duration_s

    failure_reasons = _collect_failure_reasons(metrics)
    worker_distribution, worker_distribution_meta = _collect_worker_distribution(metrics)
    worker_stats = _collect_worker_stats(metrics, worker_distribution)
    worker_identity_known = _metric_count(metrics, "worker_identity_known", 0)
    worker_identity_missing = _metric_count(metrics, "worker_identity_missing", 0)
    worker_identity_generic = _metric_count(metrics, "worker_identity_generic", 0)
    identity_total = worker_identity_known + worker_identity_missing
    identity_coverage_pct = (
        (worker_identity_known / identity_total) * 100.0 if identity_total > 0 else 0.0
    )
    gateway_distribution = None
    if (args.backend or "").strip().upper() == "LLMD":
        gateway_log_path = Path(args.gateway_log) if args.gateway_log else None
        pods_json_path = Path(args.llmd_pods_json) if args.llmd_pods_json else None
        pod_ip_map = _load_llmd_pod_ip_map(pods_json_path) if pods_json_path else {}
        gateway_distribution = _aggregate_llmd_gateway_logs(
            gateway_log_path,
            pod_ip_map,
            started_at,
            ended_at,
        )

    slo = {
        "p95_ms": float(args.slo_p95_ms),
        "error_rate_max": float(args.slo_error_rate_max),
    }
    result = {
        "profile": args.profile,
        "target_requests": int(args.target_requests),
        "requests_attempted": int(attempted),
        "requests_succeeded": int(successful),
        "requests_failed": int(failed),
        "error_rate": float(round(error_rate, 6)),
        "latency_ms": {
            "p50": float(round(p50, 3)),
            "p95": float(round(p95, 3)),
            "p99": float(round(p99, 3)),
        },
        "throughput_rps": float(round(throughput, 6)),
        "backend_mode": args.backend,
        "target_url": args.target,
        "started_at": started_at,
        "ended_at": ended_at,
        "failure_reasons": failure_reasons,
        "worker_distribution": {},
        "worker_distribution_pct": {},
        "worker_distribution_meta": {},
        "worker_identity": {
            "known": int(worker_identity_known),
            "missing": int(worker_identity_missing),
            "generic": int(worker_identity_generic),
            "coverage_pct": float(round(identity_coverage_pct, 4)),
        },
        "worker_stats": {},
    }
    (
        worker_distribution,
        worker_distribution_meta,
        worker_stats,
    ) = _merge_gateway_distribution(
        result,
        worker_distribution,
        worker_distribution_meta,
        worker_stats,
        gateway_distribution,
    )

    worker_total = sum(worker_distribution.values())
    worker_distribution_pct = {}
    for label, count in worker_distribution.items():
        if worker_total > 0:
            worker_distribution_pct[label] = round((count / worker_total) * 100.0, 4)
        else:
            worker_distribution_pct[label] = 0.0

    result["worker_distribution"] = worker_distribution
    result["worker_distribution_pct"] = worker_distribution_pct
    result["worker_distribution_meta"] = worker_distribution_meta
    result["worker_stats"] = worker_stats
    result["slo"] = slo
    result["slo_pass"] = result["latency_ms"]["p95"] <= slo["p95_ms"] and result[
        "error_rate"
    ] <= slo["error_rate_max"]

    output_json = Path(args.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, indent=2), encoding="utf-8")

    output_md = Path(args.output_md)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(_build_markdown(result, failure_reasons, slo), encoding="utf-8")


if __name__ == "__main__":
    main()
