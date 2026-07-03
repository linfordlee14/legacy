"""Unit tests for the policy matrix, ceilings, and agent rules (no database)."""

import asyncio
from typing import Any, cast

import pytest

from legacy_api.policy import (
    POLICY_VERSION,
    Action,
    AuthzContext,
    Resource,
    agent_context,
    check_agent_tool,
    decide,
    tier_at_most,
)

NO_CONN = cast(Any, None)  # decide() touches the connection only for trusted scopes

OWNER = AuthzContext(kind="owner", ceiling="P3", user_id="u-owner")
STEWARD = AuthzContext(kind="steward", ceiling="P2", user_id="u-steward")
PRE_STEWARD = AuthzContext(kind="steward_preactivation", ceiling="P1", user_id="u-s2")
PUBLIC = AuthzContext(kind="public", ceiling="P0", user_id=None)


def run(coro: Any) -> Any:
    return asyncio.run(coro)


class TestTierOrder:
    def test_ordering(self) -> None:
        assert tier_at_most("P0", "P3")
        assert tier_at_most("P2", "P2")
        assert not tier_at_most("P3", "P2")


class TestRoleMatrix:
    def test_owner_has_every_action(self) -> None:
        for action in Action:
            assert run(decide(NO_CONN, OWNER, action)).allow, action

    @pytest.mark.parametrize(
        "action",
        [Action.TIER_CHANGE, Action.GRANT_CREATE, Action.PUBLISH, Action.CONTENT_CREATE],
    )
    def test_steward_lacks_owner_only_actions(self, action: Action) -> None:
        decision = run(decide(NO_CONN, STEWARD, action))
        assert not decision.allow
        assert decision.reason == "role_lacks_action"

    @pytest.mark.parametrize(
        "action",
        [Action.UNPUBLISH, Action.VAULT_EXPORT, Action.AGENT_APPROVE, Action.GRANT_REVOKE],
    )
    def test_steward_post_activation_permissions(self, action: Action) -> None:
        assert run(decide(NO_CONN, STEWARD, action)).allow

    def test_pre_activation_steward_is_reader_only(self) -> None:
        assert run(decide(NO_CONN, PRE_STEWARD, Action.CONTENT_READ)).allow
        assert not run(decide(NO_CONN, PRE_STEWARD, Action.VAULT_EXPORT)).allow

    def test_public_reads_only(self) -> None:
        assert run(decide(NO_CONN, PUBLIC, Action.CONTENT_READ)).allow
        for action in set(Action) - {Action.CONTENT_READ}:
            assert not run(decide(NO_CONN, PUBLIC, action)).allow, action

    def test_unknown_role_denied_by_default(self) -> None:
        ghost = AuthzContext(kind="ghost", ceiling="P3", user_id="u")
        assert not run(decide(NO_CONN, ghost, Action.CONTENT_READ)).allow


class TestCeilings:
    def test_above_ceiling_denied(self) -> None:
        resource = Resource(entity_type="Note", entity_id=None, privacy_tier="P2")
        decision = run(decide(NO_CONN, PUBLIC, Action.CONTENT_READ, resource))
        assert not decision.allow
        assert decision.reason == "above_ceiling"

    def test_owner_reads_sealed(self) -> None:
        resource = Resource(entity_type="JournalEntry", entity_id=None, privacy_tier="P3")
        assert run(decide(NO_CONN, OWNER, Action.CONTENT_READ, resource)).allow

    def test_unknown_tier_denied(self) -> None:
        resource = Resource(entity_type="Note", entity_id=None, privacy_tier="P9")
        assert not run(decide(NO_CONN, OWNER, Action.CONTENT_READ, resource)).allow


class TestAgentRules:
    def test_agent_inherits_ceiling(self) -> None:
        ctx = agent_context(OWNER, "ingestion")
        assert ctx.ceiling == "P3"
        assert ctx.agent_name == "ingestion"

    def test_forbidden_actions_do_not_exist_for_agents(self) -> None:
        ctx = agent_context(OWNER, "verification")
        for action in (Action.TIER_CHANGE, Action.GRANT_CREATE, Action.SEAL_CHANGE):
            decision = run(decide(NO_CONN, ctx, action))
            assert not decision.allow
            assert decision.reason == "agent_forbidden_action"

    def test_agent_content_creation_within_principal_powers(self) -> None:
        assert run(decide(NO_CONN, agent_context(OWNER, "writing"), Action.CONTENT_CREATE)).allow

    def test_unknown_agent_identity_rejected(self) -> None:
        with pytest.raises(ValueError):
            agent_context(OWNER, "hermes")

    def test_tool_allowlists_fail_closed(self) -> None:
        assert check_agent_tool("research", "web_research")
        assert not check_agent_tool("research", "object_storage")
        assert not check_agent_tool("twin", "web_research")
        assert not check_agent_tool("unknown-agent", "anything")

    def test_decisions_carry_policy_version(self) -> None:
        assert run(decide(NO_CONN, OWNER, Action.CONTENT_READ)).policy_version == POLICY_VERSION
