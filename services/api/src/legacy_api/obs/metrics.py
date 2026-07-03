"""Metrics (OBS-07, OBS-08): a per-app Prometheus registry.

Baseline instruments: request latency and outcomes per route group, and the
token-spend counter that the model router feeds when AI calls arrive (the
primary cost-control signal, dormant until then). Product and AI metrics
join with their features; cardinality stays bounded (no per-entity labels).
"""

from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest


class Metrics:
    def __init__(self) -> None:
        self.registry = CollectorRegistry()
        self.requests = Counter(
            "legacy_api_requests_total",
            "API requests",
            labelnames=("method", "route_group", "status_code"),
            registry=self.registry,
        )
        self.request_latency = Histogram(
            "legacy_api_request_seconds",
            "API request latency",
            labelnames=("method", "route_group"),
            registry=self.registry,
            buckets=(0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 1.5, 3.0, 10.0),
        )
        # OBS-08: fed by the model router when it ships (MVP-024/TASK-301).
        self.tokens_spent = Counter(
            "legacy_ai_tokens_total",
            "Model tokens spent",
            labelnames=("provider", "model", "direction"),
            registry=self.registry,
        )

    def observe_request(
        self, method: str, route_group: str, status_code: int, duration_s: float
    ) -> None:
        self.requests.labels(method, route_group, str(status_code)).inc()
        self.request_latency.labels(method, route_group).observe(duration_s)

    def record_tokens(self, provider: str, model: str, direction: str, count: int) -> None:
        self.tokens_spent.labels(provider, model, direction).inc(count)

    def render(self) -> bytes:
        return generate_latest(self.registry)
