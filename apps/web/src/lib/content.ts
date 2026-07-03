/** Content collection reads for the workspace shell (API_SPECIFICATION 4.4). */

import { ApiError, type PageOf } from "./api";

const baseUrl = () => process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type ClaimProvenance = {
  claim_id: string;
  tier: string;
  predicate: string;
  sources: { source_id: string; label: string; url: string | null }[];
};

export type ContentItem = {
  id: string;
  title?: string | null;
  body?: string;
  canonical_markdown?: string | null;
  artifact_type?: string;
  extraction_status?: string;
  note_context?: string | null;
  privacy_tier: string;
  created_at: string;
  updated_at: string;
  provenance?: { claims: ClaimProvenance[] };
};

async function authed<T>(path: string, token: string | null): Promise<T> {
  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`${baseUrl()}${path}`, { headers });
  if (!response.ok) {
    let code = "internal";
    let message = "Request failed.";
    try {
      const body = await response.json();
      code = body.error.code;
      message = body.error.message;
    } catch {
      // defaults
    }
    throw new ApiError(response.status, code, message);
  }
  return (await response.json()) as T;
}

export function listContent(
  collection: "notes" | "artifacts",
  token: string | null,
): Promise<PageOf<ContentItem>> {
  return authed(`/v1/${collection}`, token);
}

export function getContent(
  collection: "notes" | "artifacts",
  id: string,
  token: string | null,
): Promise<ContentItem> {
  return authed(`/v1/${collection}/${id}`, token);
}
