"use client";

/**
 * Unified search screen (MVP-018; UI_UX 4.1; FS-004): mode selection,
 * SearchResult rows with type, tier, and ConfidenceBadge, snippet term
 * highlighting, citation chips, an explicit degraded indicator, and a
 * zero-result state that suggests broader scopes without fabricating.
 * Results and status changes are announced through a polite live region;
 * badges carry text labels (NFR-043).
 */

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

import { ConfidenceBadge, PrivacyTierIndicator } from "@/components/badges";
import { CitationChip } from "@/components/CitationChip";
import { ApiError } from "@/lib/api";
import {
  SEARCH_MODES,
  highlightSegments,
  searchCorpus,
  type SearchMode,
  type SearchResponse,
  type SearchResult,
} from "@/lib/search";
import { useSession } from "@/lib/session";

const COLLECTION_OF: Record<string, string> = { Note: "notes", Artifact: "artifacts" };

const MATCH_LABEL: Record<string, string> = {
  lexical: "keyword match",
  semantic: "semantic match",
};

function detailHref(result: SearchResult): string | null {
  const collection = COLLECTION_OF[result.entity_type];
  return collection ? `/library/${collection}/${result.entity_id}` : null;
}

function ResultRow({ result, query }: { result: SearchResult; query: string }) {
  const href = detailHref(result);
  const title = result.title || `Untitled ${result.entity_type.toLowerCase()}`;
  const claims = result.provenance?.claims ?? [];
  return (
    <li className="search-result">
      <article aria-label={title}>
        <div className="detail-header">
          <h3>{href ? <Link href={href}>{title}</Link> : title}</h3>
          <PrivacyTierIndicator tier={result.privacy_tier} />
        </div>
        {result.heading_path && <p className="hint">{result.heading_path}</p>}
        <p className="snippet">
          {highlightSegments(result.snippet, query).map((segment, index) =>
            segment.highlight ? (
              <mark key={index}>{segment.text}</mark>
            ) : (
              <span key={index}>{segment.text}</span>
            ),
          )}
        </p>
        <p className="hint">
          {result.entity_type} · {result.matched.map((m) => MATCH_LABEL[m] ?? m).join(" + ")}
        </p>
        {claims.length > 0 && (
          <ul className="result-claims" aria-label="Claims about this item">
            {claims.map((claim) => (
              <li key={claim.claim_id}>
                <ConfidenceBadge tier={claim.tier} /> {claim.predicate}{" "}
                <CitationChip claim={claim} />
              </li>
            ))}
          </ul>
        )}
      </article>
    </li>
  );
}

export default function SearchPage() {
  const { token } = useSession();
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<SearchMode>("hybrid");
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
    const focus = () => inputRef.current?.focus();
    window.addEventListener("legacy:search-focus", focus);
    return () => window.removeEventListener("legacy:search-focus", focus);
  }, []);

  const run = useCallback(
    async (q: string, m: SearchMode) => {
      if (!q.trim()) return;
      setBusy(true);
      setError(null);
      try {
        setResponse(await searchCorpus(q, m, token));
      } catch (caught) {
        setResponse(null);
        setError(
          caught instanceof ApiError ? caught.message : "Search is unavailable right now.",
        );
      } finally {
        setBusy(false);
      }
    },
    [token],
  );

  function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    void run(query, mode);
  }

  function onModeChange(next: SearchMode) {
    setMode(next);
    // Re-rank the current query under the newly selected mode.
    if (response || query.trim()) void run(query, next);
  }

  const status = busy
    ? "Searching."
    : response
      ? `${response.results.length} result${response.results.length === 1 ? "" : "s"} for "${response.query}" (${response.mode}).`
      : "";

  return (
    <section aria-labelledby="search-heading">
      <h1 id="search-heading">Search</h1>

      <form onSubmit={onSubmit} className="search-form" role="search">
        <label htmlFor="search-query">Search your records</label>
        <div className="search-row">
          <input
            id="search-query"
            ref={inputRef}
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="hackathon projects using YOLOv5"
            autoComplete="off"
          />
          <button type="submit" disabled={busy || !query.trim()}>
            Search
          </button>
        </div>

        <fieldset className="mode-group">
          <legend>Search mode</legend>
          {SEARCH_MODES.map((option) => (
            <label key={option.value} className="mode-option">
              <input
                type="radio"
                name="mode"
                value={option.value}
                checked={mode === option.value}
                onChange={() => onModeChange(option.value)}
              />
              {option.label} <span className="hint">({option.hint})</span>
            </label>
          ))}
        </fieldset>
      </form>

      <p role="status" aria-live="polite" className="search-status">
        {status}
      </p>

      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}

      {response?.degraded && (
        <p role="status" className="degraded-banner">
          Semantic ranking is unavailable right now; showing keyword matches only.
        </p>
      )}

      {response?.truncated && (
        <p role="status" className="hint">
          Your query was long, so it was shortened before searching.
        </p>
      )}

      {response && response.results.length === 0 && (
        <div className="zero-results">
          <p>No results in your records for &ldquo;{response.query}&rdquo;.</p>
          <p className="hint">
            Try fewer or broader words, another search mode, or browse the{" "}
            <Link href="/library">library</Link>. Nothing is ever invented to fill
            this space.
          </p>
        </div>
      )}

      {response && response.results.length > 0 && (
        <ol className="search-results" aria-label="Search results">
          {response.results.map((result) => (
            <ResultRow key={result.chunk_id} result={result} query={response.query} />
          ))}
        </ol>
      )}
    </section>
  );
}
