"""Redaction filter (OBS-03 to OBS-05).

The absolute rule: content never appears in logs, only IDs, tiers, counts,
durations, and enum-like reason codes. The filter enforces a field allowlist,
strips known content-bearing fields, pattern-scrubs residual values (emails,
bearer tokens, long free text), and fails closed: an event that cannot be
redacted safely is dropped and replaced by a warn about the drop.
"""

import logging
import re
from typing import Any

# Fields that may pass through untouched when their values also pass the
# value rules below.
ALLOWED_KEYS = {
    "event", "service", "environment", "version", "level", "request_id",
    "trace_id", "span", "parent_span", "status", "route", "method",
    "status_code", "reason", "code", "action", "tier", "policy_version",
    "provider", "model", "agent", "tool", "sev", "alert", "channel",
    "outcome", "new_device", "mfa", "queued", "kind", "principal_kind",
    "ceiling",
}
ALLOWED_SUFFIXES = (
    "_id", "_ids", "_hash", "_count", "_ms", "_s", "_tokens", "_rate",
    "_total", "_percent", "_version",
)
# Known content-bearing keys are stripped unconditionally (OBS-03): query,
# prompt, chunk, model output, bodies, statements, names of uploaded files.
FORBIDDEN_KEYS = {
    "query", "prompt", "text", "content", "body", "statement", "chunk",
    "chunk_text", "message_text", "output", "answer", "transcript",
    "filename", "file_name", "title", "email", "subject_text", "user_agent",
}

EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
TOKEN_PATTERN = re.compile(r"(?:bearer\s+)?[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{6,}", re.I)
MAX_VALUE_LENGTH = 64
MAX_MESSAGE_LENGTH = 120

_STANDARD_ATTRS = set(
    logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys()
) | {"taskName", "message", "asctime"}


def scrub_value(value: Any) -> Any | None:
    """Return a safe rendition of a value, or None when it must be dropped."""
    if isinstance(value, bool | int | float) or value is None:
        return value
    if not isinstance(value, str):
        return None  # structured objects are content risks; drop
    scrubbed = EMAIL_PATTERN.sub("[email]", value)
    scrubbed = TOKEN_PATTERN.sub("[token]", scrubbed)
    if len(scrubbed) > MAX_VALUE_LENGTH:
        return None
    return scrubbed


class RedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            self._redact(record)
            return True
        except Exception:
            # Fail closed (OBS-05): never emit an event we could not redact.
            logging.getLogger("legacy_api.obs").warning(
                "log event dropped by redaction", extra={"event": "redaction_drop"}
            )
            return False

    def _redact(self, record: logging.LogRecord) -> None:
        message = record.getMessage()
        message = EMAIL_PATTERN.sub("[email]", message)
        message = TOKEN_PATTERN.sub("[token]", message)
        if len(message) > MAX_MESSAGE_LENGTH:
            message = message[:MAX_MESSAGE_LENGTH] + "[truncated]"
        record.msg = message
        record.args = ()

        dropped = []
        for key in list(record.__dict__.keys()):
            if key in _STANDARD_ATTRS:
                continue
            value = record.__dict__[key]
            allowed_key = key in ALLOWED_KEYS or key.endswith(ALLOWED_SUFFIXES)
            if not allowed_key or key in FORBIDDEN_KEYS:
                del record.__dict__[key]
                dropped.append(key)
                continue
            safe = scrub_value(value)
            if safe is None and value is not None:
                del record.__dict__[key]
                dropped.append(key)
            else:
                record.__dict__[key] = safe
        if dropped:
            record.__dict__["redacted_field_count"] = len(dropped)
