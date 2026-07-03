"""Central authorization policy service (AUTHORIZATION 4.1 to 4.5, 4.7).

One decision service, versioned policies, deny by default. Every enforcement
point (API today; retrieval, export, and UI as they arrive) calls decide() so
the four points can never drift apart (4.4). Every denial and every sensitive
allow is audited with the policy version that produced it (4.7, NFR-030).
"""

import logging
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from fastapi import HTTPException, Request
from psycopg import AsyncConnection
from psycopg.rows import dict_row, tuple_row

from legacy_api.audit import write_audit_event
from legacy_api.auth import Principal

logger = logging.getLogger("legacy_api.policy")

POLICY_VERSION = "1"

TIER_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


def tier_at_most(tier: str, ceiling: str) -> bool:
    return TIER_ORDER[tier] <= TIER_ORDER[ceiling]


class Action(StrEnum):
    """The permission-matrix action classes of AUTHORIZATION 4.2."""

    CONTENT_READ = "content_read"
    CONTENT_CREATE = "content_create"
    CONTENT_UPDATE = "content_update"
    SOFT_DELETE = "soft_delete"
    TIER_CHANGE = "tier_change"
    SEAL_CHANGE = "seal_change"
    GRANT_CREATE = "grant_create"
    GRANT_REVOKE = "grant_revoke"
    AGENT_APPROVE = "agent_approve"
    PUBLISH = "publish"
    UNPUBLISH = "unpublish"
    VAULT_EXPORT = "vault_export"
    REDACT = "redact"
    AUDIT_READ = "audit_read"
    CURATION_ANNOTATE = "curation_annotate"


# Sensitive allows are audited (4.7); reads are not (volume).
SENSITIVE_ACTIONS = {
    Action.TIER_CHANGE, Action.SEAL_CHANGE, Action.GRANT_CREATE, Action.GRANT_REVOKE,
    Action.AGENT_APPROVE, Action.PUBLISH, Action.UNPUBLISH, Action.VAULT_EXPORT,
    Action.REDACT,
}

# Permissions never available to agent identities, independent of the
# invoking principal (4.5: 'those permissions simply do not exist').
AGENT_FORBIDDEN = {
    Action.TIER_CHANGE, Action.SEAL_CHANGE, Action.GRANT_CREATE, Action.GRANT_REVOKE,
    Action.PUBLISH, Action.AGENT_APPROVE, Action.REDACT, Action.VAULT_EXPORT,
}

# Role permission matrix (4.2). Owner column is everything by construction.
ROLE_ACTIONS: dict[str, set[Action]] = {
    "owner": set(Action),
    "steward": {
        Action.CONTENT_READ, Action.CURATION_ANNOTATE, Action.GRANT_REVOKE,
        Action.AGENT_APPROVE, Action.UNPUBLISH, Action.VAULT_EXPORT,
        Action.REDACT, Action.AUDIT_READ,
    },
    "trusted": {Action.CONTENT_READ},
    "public": {Action.CONTENT_READ},
    # Machine principals (PATs, step 9) read by default; write scopes widen
    # this per token when PATs ship. Dormant until then.
    "machine": {Action.CONTENT_READ},
}

# Per-agent tool allowlists (MULTI_AGENT_ARCHITECTURE 4.1); enforcement fails
# closed and alerts (4.5). Tools are named; unknown tools are denied.
AGENT_TOOL_ALLOWLISTS: dict[str, set[str]] = {
    "orchestrator": {"task_queue", "agent_dispatch"},
    "ingestion": {"parser", "ocr", "transcription", "github_connector", "object_storage"},
    "curation": {"search", "similarity", "taxonomy"},
    "graph": {"entity_extraction", "graph_store"},
    "timeline": {"date_parsing", "graph_store"},
    "retrieval": {"vector_index", "lexical_index"},
    "twin": {"retrieval", "memory_read"},
    "mentor": {"retrieval", "memory_read"},
    "research": {"web_research", "web_fetch"},
    "writing": {"retrieval", "templates"},
    "verification": {"research_results", "source_archive"},
    "reflection": {"memory_store", "retrieval"},
}


@dataclass(frozen=True)
class GrantScope:
    scope_type: str  # global | collection | entity
    ref_type: str | None
    ref_id: str | None


@dataclass(frozen=True)
class AuthzContext:
    """The resolved authorization identity of one request."""

    kind: str  # owner | steward | steward_preactivation | trusted | public | machine
    ceiling: str  # P0..P3
    user_id: str | None
    scopes: tuple[GrantScope, ...] = field(default_factory=tuple)
    agent_name: str | None = None  # set when an agent acts on behalf (4.5)

    @property
    def role_key(self) -> str:
        if self.kind == "steward_preactivation":
            return "trusted"  # pre-activation: P1 reader, no elevated permissions
        return self.kind


@dataclass(frozen=True)
class Resource:
    entity_type: str
    entity_id: str | None
    privacy_tier: str


@dataclass(frozen=True)
class Decision:
    allow: bool
    reason: str
    policy_version: str = POLICY_VERSION


PUBLIC_CONTEXT = AuthzContext(kind="public", ceiling="P0", user_id=None)


async def resolve_context(
    conn: AsyncConnection[Any], principal: Principal | None
) -> AuthzContext:
    """Resolve a principal into its authorization context (4.1, 4.3).

    Grants are read live so revocation is immediate (4.3): the decision point
    checks current rows, never token-issuance-time state.
    """
    if principal is None:
        return PUBLIC_CONTEXT
    if principal.is_owner:
        return AuthzContext(kind="owner", ceiling="P3", user_id=principal.user_id)

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT r.name AS role_name, r.max_privacy_tier,
                   g.scope_type, g.scope_ref_type, g.scope_ref_id,
                   g.activation_condition
            FROM access_grant g
            JOIN role r ON r.id = g.role_id AND r.deleted_at IS NULL
            WHERE g.user_id = %s
              AND g.deleted_at IS NULL
              AND (g.expires_at IS NULL OR g.expires_at > now())
            """,
            (principal.user_id,),
        )
        rows = await cur.fetchall()

    steward_rows = [r for r in rows if r["role_name"] == "steward"]
    if steward_rows:
        # Succession activation semantics live in SECURITY; until a condition
        # is evaluated as met by that machinery, a conditioned steward grant
        # confers only the pre-activation ceiling (AUTHORIZATION 4.1).
        activated = any(r["activation_condition"] is None for r in steward_rows)
        if activated:
            return AuthzContext(kind="steward", ceiling="P2", user_id=principal.user_id)
        return AuthzContext(
            kind="steward_preactivation", ceiling="P1", user_id=principal.user_id
        )

    trusted_rows = [r for r in rows if r["role_name"] == "trusted"]
    if trusted_rows:
        scopes = tuple(
            GrantScope(
                scope_type=r["scope_type"],
                ref_type=r["scope_ref_type"],
                ref_id=str(r["scope_ref_id"]) if r["scope_ref_id"] else None,
            )
            for r in trusted_rows
        )
        return AuthzContext(
            kind="trusted", ceiling="P1", user_id=principal.user_id, scopes=scopes
        )

    # Authenticated human with no grants: no matrix row grants access beyond
    # public; deny by default means the public ceiling applies.
    return AuthzContext(kind="public", ceiling="P0", user_id=principal.user_id)


async def _scope_covers(
    conn: AsyncConnection[Any], scopes: tuple[GrantScope, ...], resource: Resource
) -> bool:
    """Does any grant scope cover the resource (4.3)?

    Entity scopes cover the entity itself and items linked to it by
    membership-style edges (member_of, tagged_with); collection scopes cover
    collection members. Global scopes cover everything within the ceiling.
    """
    for scope in scopes:
        if scope.scope_type == "global":
            return True
        if resource.entity_id is None:
            continue
        if (
            scope.scope_type == "entity"
            and scope.ref_type == resource.entity_type
            and scope.ref_id == resource.entity_id
        ):
            return True
        target_type = "Collection" if scope.scope_type == "collection" else scope.ref_type
        async with conn.cursor(row_factory=tuple_row) as cur:
            await cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1 FROM edge
                    WHERE from_type = %s AND from_id = %s
                      AND to_type = %s AND to_id = %s
                      AND edge_type IN ('member_of', 'tagged_with')
                      AND deleted_at IS NULL
                )
                """,
                (resource.entity_type, resource.entity_id, target_type, scope.ref_id),
            )
            row = await cur.fetchone()
        if row and row[0]:
            return True
    return False


async def decide(
    conn: AsyncConnection[Any],
    ctx: AuthzContext,
    action: Action,
    resource: Resource | None = None,
) -> Decision:
    """The single decision function behind every enforcement point (4.4).

    Deny by default: anything not explicitly allowed by the matrix, ceiling,
    and scope rules is denied.
    """
    # Agent identities: forbidden actions do not exist for them (4.5),
    # regardless of the invoking principal.
    if ctx.agent_name is not None and action in AGENT_FORBIDDEN:
        return Decision(allow=False, reason="agent_forbidden_action")

    allowed_actions = ROLE_ACTIONS.get(ctx.role_key, set())
    if action not in allowed_actions:
        return Decision(allow=False, reason="role_lacks_action")

    if resource is not None:
        if resource.privacy_tier not in TIER_ORDER:
            return Decision(allow=False, reason="unknown_tier")
        if not tier_at_most(resource.privacy_tier, ctx.ceiling):
            return Decision(allow=False, reason="above_ceiling")
        if ctx.kind == "trusted" and not await _scope_covers(conn, ctx.scopes, resource):
            return Decision(allow=False, reason="outside_grant_scope")

    return Decision(allow=True, reason="allowed")


async def authorize(
    conn: AsyncConnection[Any],
    ctx: AuthzContext,
    action: Action,
    resource: Resource | None = None,
    request_id: str | None = None,
) -> Decision:
    """decide() plus the 4.7 audit obligations.

    Denials always audit; sensitive allows audit too. The audit row carries
    the policy version that produced the decision.
    """
    decision = await decide(conn, ctx, action, resource)
    should_audit = (not decision.allow) or (action in SENSITIVE_ACTIONS)
    if should_audit:
        await write_audit_event(
            conn,
            actor_type="agent" if ctx.agent_name else "user",
            actor_id=ctx.user_id,
            action="authz_denied" if not decision.allow else "authz_sensitive_allow",
            subject_type=resource.entity_type if resource else None,
            subject_id=resource.entity_id if resource else None,
            payload={
                "requested_action": action.value,
                "reason": decision.reason,
                "policy_version": decision.policy_version,
                "principal_kind": ctx.kind,
                "ceiling": ctx.ceiling,
                **({"agent_name": ctx.agent_name} if ctx.agent_name else {}),
            },
            request_id=request_id,
        )
        await conn.commit()
    if not decision.allow:
        logger.warning(
            "authorization denied",
            extra={
                "reason": decision.reason,
                "action": action.value,
                "principal_kind": ctx.kind,
                "policy_version": decision.policy_version,
            },
        )
    return decision


def check_agent_tool(agent_name: str, tool: str) -> bool:
    """Per-agent tool allowlist (4.5): out-of-list tools fail closed and are
    logged for alerting; callers must treat False as a hard stop."""
    allowed = tool in AGENT_TOOL_ALLOWLISTS.get(agent_name, set())
    if not allowed:
        logger.warning(
            "agent tool denied (fail closed)",
            extra={"agent": agent_name, "tool": tool, "policy_version": POLICY_VERSION},
        )
    return allowed


def agent_context(ctx: AuthzContext, agent_name: str) -> AuthzContext:
    """An agent acting on behalf of a principal inherits the principal's
    ceiling and can never exceed it (4.5, NFR-031)."""
    if agent_name not in AGENT_TOOL_ALLOWLISTS:
        raise ValueError(f"unknown agent identity: {agent_name}")
    return AuthzContext(
        kind=ctx.kind,
        ceiling=ctx.ceiling,
        user_id=ctx.user_id,
        scopes=ctx.scopes,
        agent_name=agent_name,
    )


def raise_uniform_not_found() -> HTTPException:
    """The single not-found error for both 'missing' and 'above ceiling'
    (4.4 point 1: existence itself is never leaked)."""
    return HTTPException(status_code=404, detail={"code": "not_found", "message": "Not found."})


async def read_or_not_found(
    conn: AsyncConnection[Any],
    ctx: AuthzContext,
    resource: Resource | None,
    request_id: str | None = None,
) -> None:
    """Enforcement-point helper for reads: missing rows and above-ceiling rows
    produce byte-identical responses; above-ceiling attempts are audited."""
    if resource is None:
        raise raise_uniform_not_found()
    decision = await authorize(
        conn, ctx, Action.CONTENT_READ, resource, request_id=request_id
    )
    if not decision.allow:
        raise raise_uniform_not_found()


def get_request_context(request: Request) -> AuthzContext | None:
    """Fetch the context resolved for this request, when middleware set one."""
    return getattr(request.state, "authz_context", None)
