"""Structured JSON logging (OBS-01, OBS-02, OBS-06).

Every line carries timestamp, level, service, environment, request and trace
identifiers, an event name, and typed fields only. Emission in production
mode is asynchronous via a queue so telemetry never blocks a request.
"""

import json
import logging
import queue
from datetime import UTC, datetime
from logging.handlers import QueueHandler, QueueListener
from typing import Any

from legacy_api.obs.redaction import _STANDARD_ATTRS, RedactionFilter
from legacy_api.obs.tracing import current_span_name, current_trace_id

SERVICE_NAME = "legacy-api"


class JsonFormatter(logging.Formatter):
    def __init__(self, environment: str) -> None:
        super().__init__()
        self.environment = environment

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(tz=UTC).isoformat(),
            "level": record.levelname.lower(),
            "service": SERVICE_NAME,
            "environment": self.environment,
            "logger": record.name,
            "message": record.getMessage(),
        }
        trace_id = current_trace_id()
        if trace_id and "trace_id" not in record.__dict__:
            payload["trace_id"] = trace_id
        span = current_span_name()
        if span and "span" not in record.__dict__:
            payload["span"] = span
        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRS:
                payload[key] = value
        return json.dumps(payload, default=str)


def setup_logging(environment: str, level: str = "info", async_mode: bool = True) -> None:
    """Configure the legacy_api logger tree; idempotent."""
    logger = logging.getLogger("legacy_api")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False
    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    stream = logging.StreamHandler()
    stream.setFormatter(JsonFormatter(environment))
    stream.addFilter(RedactionFilter())

    if async_mode:
        log_queue: queue.Queue[Any] = queue.Queue(maxsize=10000)
        listener = QueueListener(log_queue, stream, respect_handler_level=True)
        listener.start()
        queue_handler = QueueHandler(log_queue)
        # Redact BEFORE the queue: the record must already be safe when it
        # leaves the request path (OBS-05, OBS-06).
        queue_handler.addFilter(RedactionFilter())
        logger.addHandler(queue_handler)
        logger.__dict__["_legacy_queue_listener"] = listener
    else:
        logger.addHandler(stream)
