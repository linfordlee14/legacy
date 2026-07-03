"""Observability baseline tests (MVP-008, OBSERVABILITY 4.1 to 4.5).

Redaction unit coverage, alert routing with quiet hours, metrics, and the
two step acceptance proofs: no P2 content reaches logs on a real request
cycle, and a traced request is reconstructable end to end.
"""

import json
import logging
import os
import time
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from legacy_api.auth import LogNotifier
from legacy_api.obs.alerts import AlertRouter, Severity, send_test_alert
from legacy_api.obs.logging import JsonFormatter
from legacy_api.obs.metrics import Metrics
from legacy_api.obs.redaction import RedactionFilter, scrub_value
from legacy_api.obs.tracing import route_group

DB_URL = os.environ.get("LEGACY_TEST_DATABASE_URL")


def make_record(msg: str = "event", **extra: Any) -> logging.LogRecord:
    record = logging.LogRecord("legacy_api.test", logging.INFO, __file__, 1, msg, (), None)
    for key, value in extra.items():
        record.__dict__[key] = value
    return record


class RecordingNotifier:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    def notify(self, subject: str, body: str) -> None:
        self.messages.append((subject, body))


class TestRedaction:
    def test_forbidden_and_unlisted_fields_dropped(self) -> None:
        record = make_record(
            query="private words", note_id="n1", token_count=5, reason="ok", mystery="x"
        )
        assert RedactionFilter().filter(record)
        assert "query" not in record.__dict__
        assert "mystery" not in record.__dict__
        assert record.__dict__["note_id"] == "n1"
        assert record.__dict__["token_count"] == 5
        assert record.__dict__["redacted_field_count"] == 2

    def test_email_and_token_scrubbed_in_allowed_fields(self) -> None:
        record = make_record(reason="mail bob@example.com sent")
        RedactionFilter().filter(record)
        assert record.__dict__["reason"] == "mail [email] sent"
        assert scrub_value("Bearer abcdefghijklmnopqrstuvwx1234.signature") == "[token]"

    def test_long_values_dropped(self) -> None:
        record = make_record(reason="x" * 200)
        RedactionFilter().filter(record)
        assert "reason" not in record.__dict__

    def test_structured_values_dropped(self) -> None:
        record = make_record(code={"nested": "object"})
        RedactionFilter().filter(record)
        assert "code" not in record.__dict__

    def test_message_scrubbed_and_truncated(self) -> None:
        record = make_record(msg="notify owner@example.test " + "y" * 200)
        RedactionFilter().filter(record)
        assert "[email]" in record.getMessage()
        assert "[truncated]" in record.getMessage()
        assert "owner@example.test" not in record.getMessage()

    def test_fails_closed_on_unrenderable_event(self) -> None:
        class Boom:
            def __str__(self) -> str:
                raise RuntimeError("no")

        record = make_record()
        record.msg = Boom()
        assert RedactionFilter().filter(record) is False


class TestAlerts:
    def test_severity_routing_and_quiet_hours(self) -> None:
        notifier = RecordingNotifier()
        router = AlertRouter(notifier=notifier, quiet_start_hour=22, quiet_end_hour=6)
        quiet = datetime(2026, 7, 3, 23, 0, tzinfo=UTC)
        awake = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)

        assert router.send(Severity.SEV2, "budget", "80 percent", now=quiet) is False
        assert notifier.messages == []
        assert router.send(Severity.SEV1, "down", "probe failing", now=quiet) is True
        assert notifier.messages[0][0] == "[SEV-1] down"
        assert router.send(Severity.SEV2, "budget", "80 percent", now=awake) is True
        assert router.flush_queue() == 1
        assert len(notifier.messages) == 3

    def test_test_alert_reaches_owner_channel(self) -> None:
        notifier = RecordingNotifier()
        assert send_test_alert(AlertRouter(notifier=notifier)) is True
        subject, body = notifier.messages[0]
        assert subject == "[SEV-2] test-alert"
        assert "Runbook" in body

    def test_log_channel_notifier_works(self) -> None:
        send_test_alert(AlertRouter(notifier=LogNotifier()))


class TestMetricsAndGrouping:
    def test_request_metrics_render(self) -> None:
        metrics = Metrics()
        metrics.observe_request("GET", "/v1/claims", 200, 0.05)
        metrics.record_tokens("anthropic", "claude", "input", 100)
        output = metrics.render().decode()
        assert "legacy_api_requests_total" in output
        assert "legacy_ai_tokens_total" in output

    def test_route_group_bounds_cardinality(self) -> None:
        assert route_group("/v1/claims/123-abc") == "/v1/claims"
        assert route_group("/v1/claims") == "/v1/claims"
        assert route_group("/healthz") == "/healthz"


@pytest.mark.skipif(not DB_URL, reason="LEGACY_TEST_DATABASE_URL not set")
class TestEndToEnd:
    SECRET = "XYZZY-P2-SECRET-CONTENT"

    @pytest.fixture(scope="class")
    def env(self) -> Iterator[Any]:
        import jwt as pyjwt
        import psycopg
        from alembic import command
        from alembic.config import Config
        from cryptography.hazmat.primitives.asymmetric import rsa
        from fastapi.testclient import TestClient

        from legacy_api.config import Settings
        from legacy_api.main import create_app
        from legacy_api.verifier import TokenVerifier

        api_dir = Path(__file__).resolve().parent.parent
        cfg = Config(str(api_dir / "alembic.ini"))
        cfg.set_main_option("script_location", str(api_dir / "migrations"))
        os.environ["LEGACY_DATABASE_URL"] = DB_URL or ""
        system = "00000000-0000-7000-8000-000000000001"
        issuer, audience = "https://auth.test.invalid", "legacy-api"
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        with psycopg.connect(DB_URL, autocommit=True) as conn:
            for (table,) in conn.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            ).fetchall():
                conn.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
            command.upgrade(cfg, "head")
            owner = conn.execute(
                """
                INSERT INTO app_user
                    (email, display_name, user_kind, is_owner, auth_subject, created_by)
                VALUES ('obs-owner@example.test', 'owner', 'human', true, 'obs-owner', %s)
                RETURNING id
                """,
                (system,),
            ).fetchone()[0]
            claim_id = str(
                conn.execute(
                    """
                    INSERT INTO claim (subject_type, subject_id, predicate, statement,
                                       confidence_tier, privacy_tier, created_by)
                    VALUES ('Note', %s, 'contains', %s, 'self_reported', 'P2', %s)
                    RETURNING id
                    """,
                    (str(uuid.uuid4()), self.SECRET, owner),
                ).fetchone()[0]
            )

        settings = Settings(  # type: ignore[call-arg]
            env="local", database_url=DB_URL, oidc_issuer=issuer, oidc_audience=audience
        )
        verifier = TokenVerifier(
            issuer=issuer, audience=audience, key_provider=lambda _t: key.public_key()
        )
        app = create_app(settings, verifier=verifier)

        now = int(time.time())
        token = pyjwt.encode(
            {
                "iss": issuer, "aud": audience, "sub": "obs-owner", "iat": now,
                "exp": now + 900, "auth_time": now, "session_id": "obs-s1", "aal": "aal2",
            },
            key,
            algorithm="RS256",
        )

        from types import SimpleNamespace

        with TestClient(app) as test_client:
            yield SimpleNamespace(client=test_client, token=token, claim_id=claim_id)

    @pytest.fixture()
    def captured(self, env: Any) -> Iterator[list[str]]:
        lines: list[str] = []

        class Capture(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                lines.append(self.format(record))

        handler = Capture()
        handler.setFormatter(JsonFormatter("local"))
        handler.addFilter(RedactionFilter())
        logger = logging.getLogger("legacy_api")
        logger.addHandler(handler)
        try:
            yield lines
        finally:
            logger.removeHandler(handler)

    def test_no_p2_content_reaches_logs(self, env: Any, captured: list[str]) -> None:
        headers = {"Authorization": f"Bearer {env.token}", "User-Agent": "obs-tests"}
        listing = env.client.get("/v1/claims", headers=headers)
        assert listing.status_code == 200
        single = env.client.get(f"/v1/claims/{env.claim_id}", headers=headers)
        assert single.status_code == 200
        # The P2 statement is in the API response (owner ceiling) by design.
        assert self.SECRET in single.text
        env.client.get("/v1/auth/session")  # a denied attempt logs too

        assert captured, "expected log events from the request cycle"
        for line in captured:
            assert self.SECRET not in line

    def test_traced_request_reconstructable(self, env: Any, captured: list[str]) -> None:
        trace_id = "obs-trace-1"
        response = env.client.get(
            "/v1/claims",
            headers={
                "Authorization": f"Bearer {env.token}",
                "User-Agent": "obs-tests",
                "X-Request-ID": trace_id,
            },
        )
        assert response.status_code == 200
        assert response.headers["X-Trace-ID"] == trace_id

        spans = [
            json.loads(line)
            for line in captured
            if '"span"' in line and f'"{trace_id}"' in line
        ]
        by_name = {entry["span"]: entry for entry in spans if entry.get("event") == "span"}
        assert "api.request" in by_name
        assert "db.claim_list" in by_name
        assert by_name["db.claim_list"]["parent_span"] == "api.request"
        assert by_name["api.request"]["trace_id"] == trace_id
        assert by_name["api.request"]["duration_ms"] >= 0

    def test_metrics_endpoint_counts_requests(self, env: Any) -> None:
        env.client.get("/v1/claims", headers={"Authorization": f"Bearer {env.token}"})
        output = env.client.get("/metrics").text
        assert 'route_group="/v1/claims"' in output
        assert "legacy_api_request_seconds" in output
