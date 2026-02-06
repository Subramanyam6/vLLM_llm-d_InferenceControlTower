# Stress Test Summary

## Run Metadata

- Profile: `smoke`
- Backend: `LLMD`
- Target URL: `http://127.0.0.1:8000/api/submit`
- Started: `2026-02-06T17:50:15Z`
- Ended: `2026-02-06T17:58:36Z`
- Target Requests: `50000`

## Key Metrics

| Metric | Value |
| --- | --- |
| Requests attempted | 50000 |
| Requests succeeded | 49995 |
| Requests failed | 5 |
| Error rate | 0.0001 |
| Throughput (req/s) | 99.99 |
| p50 latency (ms) | 53.05 |
| p95 latency (ms) | 186.02 |
| p99 latency (ms) | 785.08 |

## Worker Distribution (A-E)

| Worker | Requests | Share |
| --- | --- | --- |
| A | 49995 | 100.00% |
| B | 0 | 0.00% |
| C | 0 | 0.00% |
| D | 0 | 0.00% |
| E | 0 | 0.00% |

- Raw extras: other=0, missing=0, counted=49995

## Pass/Fail

- Result: **PASS**
- SLO p95 <= 2000.0 ms
- SLO error_rate <= 0.02

## Top Failure Reasons

- network: 5
