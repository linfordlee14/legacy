/**
 * Verification queue client (MVP-020; API_SPECIFICATION 4.4). Owner-only
 * surface; resolutions require a fresh authentication event server-side.
 */

import { ApiError } from "./api";

const baseUrl = () => process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type Evidence = {
  source_id: string;
  source_type: string;
  title: string;
  url: string | null;
  publisher: string | null;
  reliability_note: string | null;
  support_type: string;
  note: string | null;
};

export type QueueClaim = {
  id: string;
  subject_type: string;
  subject_id: string;
  predicate: string;
  statement: string;
  confidence_tier: string;
  tier_rationale: string | null;
  verified_at: string | null;
  review_due_at: string | null;
  privacy_tier: string;
  evidence: Evidence[];
  supporting_count: number;
  contradicting_count: number;
};

export type Queue = {
  items: QueueClaim[];
  open_flagged: number;
  stale_self_reported: number;
};

export type EvidenceInput = {
  support_type: "supports" | "contradicts";
  note?: string;
  source: {
    source_type: string;
    title: string;
    url?: string;
    publisher?: string;
    reliability_note?: string;
  };
};

export type Resolution =
  | { decision: "apply"; target_tier: "verified" | "self_reported" | "flagged"; note?: string }
  | { decision: "reject"; note?: string };

async function call<T>(path: string, token: string | null, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    ...(init?.body ? { "Content-Type": "application/json" } : {}),
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`${baseUrl()}${path}`, { ...init, headers });
  if (!response.ok) {
    let code = "internal";
    let message = "Request failed.";
    try {
      const body = await response.json();
      code = body.error.code;
      message = body.error.message;
      if (body.error.details?.reason) message = `${message} ${body.error.details.reason}`;
    } catch {
      // defaults
    }
    throw new ApiError(response.status, code, message);
  }
  return (await response.json()) as T;
}

export function getQueue(token: string | null): Promise<Queue> {
  return call("/v1/verification/queue", token);
}

export function attachEvidence(
  claimId: string,
  input: EvidenceInput,
  token: string | null,
): Promise<QueueClaim> {
  return call(`/v1/verification/claims/${claimId}/evidence`, token, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function resolveClaim(
  claimId: string,
  resolution: Resolution,
  token: string | null,
): Promise<{ outcome: string; claim: QueueClaim }> {
  return call(`/v1/verification/claims/${claimId}/resolve`, token, {
    method: "POST",
    body: JSON.stringify(resolution),
  });
}
