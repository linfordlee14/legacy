"""Owner alerting (OBS-19 to OBS-23).

The severity ladder routes to the owner's channels; channel bindings are
configuration, not spec (OBS-19), so delivery goes through the notifier
port (the structured-log channel until real channels are provisioned).
Quiet hours hold SEV-2 and below; SEV-1 always breaks through (OBS-20).
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import IntEnum

from legacy_api.auth import OwnerNotifier

logger = logging.getLogger("legacy_api.alerts")


class Severity(IntEnum):
    SEV1 = 1  # platform down or data at risk; ignores quiet hours
    SEV2 = 2  # degraded or budget threat
    SEV3 = 3  # needs attention this week
    SEV4 = 4  # informational digest material


@dataclass
class AlertRouter:
    notifier: OwnerNotifier
    quiet_start_hour: int | None = None  # owner-configured, UTC (OBS-20)
    quiet_end_hour: int | None = None
    queued: list[tuple[Severity, str, str]] = field(default_factory=list)

    def _in_quiet_hours(self, now: datetime) -> bool:
        if self.quiet_start_hour is None or self.quiet_end_hour is None:
            return False
        hour = now.hour
        if self.quiet_start_hour <= self.quiet_end_hour:
            return self.quiet_start_hour <= hour < self.quiet_end_hour
        return hour >= self.quiet_start_hour or hour < self.quiet_end_hour

    def send(
        self, severity: Severity, name: str, body: str, now: datetime | None = None
    ) -> bool:
        """Deliver or queue an alert; returns True when delivered now."""
        now = now or datetime.now(tz=UTC)
        hold = severity != Severity.SEV1 and self._in_quiet_hours(now)
        logger.warning(
            "alert",
            extra={
                "event": "alert",
                "alert": name,
                "sev": int(severity),
                "queued": hold,
            },
        )
        if hold:
            self.queued.append((severity, name, body))
            return False
        self.notifier.notify(f"[SEV-{int(severity)}] {name}", body)
        return True

    def flush_queue(self) -> int:
        """Deliver held alerts once quiet hours end (OBS-20)."""
        delivered = 0
        while self.queued:
            severity, name, body = self.queued.pop(0)
            self.notifier.notify(f"[SEV-{int(severity)}] {name}", body)
            delivered += 1
        return delivered


def send_test_alert(router: AlertRouter) -> bool:
    """The provable path from alert emission to the owner channel; used by
    `make test-alert` and the step 7 acceptance check."""
    return router.send(
        Severity.SEV2,
        "test-alert",
        "This is a Legacy observability test alert. Runbook: infra/runbooks/DEPLOY.md.",
    )


if __name__ == "__main__":  # pragma: no cover - exercised via `make test-alert`
    from legacy_api.auth import LogNotifier
    from legacy_api.obs.logging import setup_logging

    setup_logging(environment="local", async_mode=False)
    delivered = send_test_alert(AlertRouter(notifier=LogNotifier()))
    print(f"test alert delivered: {delivered}")
