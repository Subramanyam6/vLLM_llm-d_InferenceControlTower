# Stress Test Summary

## Run Metadata

- Profile: `smoke`
- Backend: `LLMD`
- Target URL: `http://127.0.0.1:8000/api/submit`
- Started: `2026-02-06T22:56:31Z`
- Ended: `2026-02-06T23:10:24Z`
- Target Requests: `100000`

## Key Metrics

| Metric | Value |
| --- | --- |
| Requests attempted | 103456 |
| Requests succeeded | 88065 |
| Requests failed | 15391 |
| Error rate | 0.1488 |
| Throughput (req/s) | 124.30 |
| p50 latency (ms) | 218.55 |
| p95 latency (ms) | 425.48 |
| p99 latency (ms) | 2019.46 |

## Worker Distribution (A-E)

| Worker | Requests | Share |
| --- | --- | --- |
| A | 88065 | 100.00% |
| B | 0 | 0.00% |
| C | 0 | 0.00% |
| D | 0 | 0.00% |
| E | 0 | 0.00% |

- Raw extras: other=0, missing=0, counted=88065

## Worker Detail Signals (A-E)

| Worker | Avg latency (ms) | p95 latency (ms) | Cache hit rate | Queue avg | Reported errors avg | Reported p95 avg (ms) | Cache warmth avg | API errors |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 258.269 | 437.288 | n/a | 0.0 | 0.0 | 478.0 | 60.0 | 0 |
| B | n/a | n/a | n/a | 0.0 | 0.0 | 0.0 | 0.0 | 0 |
| C | n/a | n/a | n/a | 0.0 | 0.0 | 0.0 | 0.0 | 0 |
| D | n/a | n/a | n/a | 0.0 | 0.0 | 0.0 | 0.0 | 0 |
| E | n/a | n/a | n/a | 0.0 | 0.0 | 0.0 | 0.0 | 0 |

## Worker Identity Coverage

- identity known: 0
- identity missing: 88065
- identity generic: 0
- identity coverage: 0.00%

## Pass/Fail

- Result: **FAIL**
- SLO p95 <= 2000.0 ms
- SLO error_rate <= 0.02

## Top Failure Reasons

- network: 15391
