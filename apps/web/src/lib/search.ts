/**
 * Search client for GET /v1/search (MVP-018 consuming the step 17 API;
 * api/API_SPECIFICATION.md 4.4). The contract is consumed exactly as
 * shipped: modes, degraded/truncated flags, and the provenance block.
 */

import { ApiError } from "./api";
import type { ClaimProvenance } from "./content";

const baseUrl = () => process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type SearchMode = "hybrid" | "lexical" | "semantic";

export const SEARCH_MODES: { value: SearchMode; label: string; hint: string }[] = [
  { value: "hybrid", label: "Hybrid", hint: "keyword and meaning, fused" },
  { value: "lexical", label: "Keyword", hint: "exact words and phrases" },
  { value: "semantic", label: "Semantic", hint: "by meaning" },
];

export type SearchResult = {
  chunk_id: string;
  chunk_ref: string;
  entity_type: string;
  entity_id: string;
  title: string | null;
  snippet: string;
  heading_path: string | null;
  privacy_tier: string;
  score: number;
  matched: string[];
  provenance: { claims: ClaimProvenance[] };
};

export type SearchResponse = {
  query: string;
  mode: SearchMode;
  degraded: boolean;
  truncated: boolean;
  results: SearchResult[];
  retrieval: {
    chunks_considered: number;
    chunks_returned: number;
    tier_ceiling: string;
  };
};

export async function searchCorpus(
  q: string,
  mode: SearchMode,
  token: string | null,
  limit = 25,
): Promise<SearchResponse> {
  const params = new URLSearchParams({ q, mode, limit: String(limit) });
  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`${baseUrl()}/v1/search?${params}`, { headers });
  if (!response.ok) {
    let code = "internal";
    let message = "Search failed.";
    try {
      const body = await response.json();
      code = body.error.code;
      message = body.error.message;
    } catch {
      // defaults
    }
    throw new ApiError(response.status, code, message);
  }
  return (await response.json()) as SearchResponse;
}

/**
 * Split a snippet into plain and highlighted segments for the query's
 * terms (semantic snippet highlighting per MVP-018). Term matching is
 * case-insensitive on words of three or more characters; the caller
 * renders highlighted segments in <mark>.
 */
export function highlightSegments(
  snippet: string,
  query: string,
): { text: string; highlight: boolean }[] {
  const terms = Array.from(
    new Set(
      query
        .split(/\s+/)
        .map((term) => term.replace(/[^\p{L}\p{N}]/gu, ""))
        .filter((term) => term.length >= 3),
    ),
  );
  if (terms.length === 0) return [{ text: snippet, highlight: false }];
  const pattern = new RegExp(
    `(${terms.map((term) => term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`,
    "giu",
  );
  return snippet
    .split(pattern)
    .filter((part) => part !== "")
    .map((part) => ({
      text: part,
      highlight: terms.some((term) => part.toLowerCase() === term.toLowerCase()),
    }));
}
