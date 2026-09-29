import statistics
import time

from src.models.risk import black_scholes


def main():
    n = 100_000
    latencies = []
    start = time.perf_counter()
    for _ in range(n):
        t0 = time.perf_counter_ns()
        black_scholes(225, 230, 0.5, 0.045, 0.25, "call")
        latencies.append((time.perf_counter_ns() - t0) / 1e6)
    elapsed = time.perf_counter() - start
    latencies.sort()
    p50 = latencies[int(0.50 * n)]
    p95 = latencies[int(0.95 * n)]
    print(f"Pricing operations: {n:,}")
    print(f"Throughput: {n / elapsed:,.0f} ops/sec")
    print(f"Latency p50: {p50:.4f} ms")
    print(f"Latency p95: {p95:.4f} ms")
    print("Note: this microbenchmark measures pricing-engine throughput, not end-to-end Kafka latency.")


if __name__ == "__main__":
    main()
