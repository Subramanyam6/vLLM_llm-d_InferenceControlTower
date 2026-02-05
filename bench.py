import statistics

from core import Gateway


def percentile(values, p):
    if not values:
        return 0.0
    values = sorted(values)
    k = int(round((p / 100.0) * (len(values) - 1)))
    return float(values[k])


def run_mode(mode):
    gateway = Gateway(worker_count=3, rate_limit_per_min=100000, retries=1)
    gateway.set_chaos(0.0, 0.0)

    prompts = [f"request {i % 5}" for i in range(40)]
    latencies = []
    for p in prompts:
        res = gateway.handle(p, "SIM", mode)
        latencies.append(res["latency_ms"])

    p50 = statistics.median(latencies)
    p95 = percentile(latencies, 95)
    print(f"{mode}: p50={int(p50)}ms p95={int(p95)}ms")


if __name__ == "__main__":
    for mode in ["round_robin", "least_queue", "cache_aware"]:
        run_mode(mode)
