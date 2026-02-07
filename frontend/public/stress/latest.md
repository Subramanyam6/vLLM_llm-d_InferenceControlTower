# Stress Test Summary

## Run Metadata

- Profile: `standard`
- Backend: `LLMD`
- Target URL: `http://127.0.0.1:8000/api/submit`
- Started: `2026-02-07T00:18:11Z`
- Ended: `2026-02-07T00:23:48Z`
- Target Requests: `100000`

## Key Metrics

| Metric | Value |
| --- | --- |
| Requests attempted | 100200 |
| Requests succeeded | 100200 |
| Requests failed | 0 |
| Error rate | 0.0000 |
| Throughput (req/s) | 300.00 |
| p50 latency (ms) | 2.46 |
| p95 latency (ms) | 3.81 |
| p99 latency (ms) | 37.92 |

## Worker Distribution (A-E)

- Source: `llmd_gateway_logs`
- Worker label mapping:
  - A -> `llm-d-modelservice-decode-589fb6d5c7-548vg` (10.244.0.61)
  - B -> `llm-d-modelservice-decode-589fb6d5c7-7w8qw` (10.244.0.66)
  - C -> `llm-d-modelservice-decode-589fb6d5c7-kl8c8` (10.244.0.67)
  - D -> `llm-d-modelservice-decode-589fb6d5c7-q8h6l` (10.244.0.59)
  - E -> `llm-d-modelservice-decode-589fb6d5c7-wlddg` (10.244.0.60)

| Worker | Requests | Share |
| --- | --- | --- |
| A | 19982 | 19.94% |
| B | 20083 | 20.04% |
| C | 20081 | 20.04% |
| D | 20067 | 20.03% |
| E | 19987 | 19.95% |

- Raw extras: other=0, missing=0, counted=100200

## Worker Detail Signals (A-E)

| Worker | Avg latency (ms) | p95 latency (ms) | Cache hit rate | Queue avg | Reported errors avg | Reported p95 avg (ms) | Cache warmth avg | API errors |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 0.002 | 0.0 | n/a | 0.0 | 0.0 | 0.0 | 0.0 | 0 |
| B | 0.002 | 0.0 | n/a | 0.0 | 0.0 | 0.0 | 0.0 | 0 |
| C | 0.002 | 0.0 | n/a | 0.0 | 0.0 | 0.0 | 0.0 | 0 |
| D | 0.002 | 0.0 | n/a | 0.0 | 0.0 | 0.0 | 0.0 | 0 |
| E | 0.003 | 0.0 | n/a | 0.0 | 0.0 | 0.0 | 0.0 | 0 |

## Worker Identity Coverage

- identity known: 100200
- identity missing: 0
- identity generic: 100200
- identity coverage: 100.00%

## Pass/Fail

- Result: **PASS**
- SLO p95 <= 2000.0 ms
- SLO error_rate <= 0.02

## Top Failure Reasons

- No failures recorded.
