"use client";

/**
 * Citation chip (UI_UX 4.4; ACCESSIBILITY 4.5): in the tab order, expands
 * via the disclosure pattern, and the expanded content is a described
 * region linking source and tier. The claim identifier is shown as text;
 * it becomes a link when the verification queue screen lands (MVP-020).
 */

import { useId, useState } from "react";

import type { ClaimProvenance } from "@/lib/content";

import { ConfidenceBadge } from "./badges";

export function CitationChip({ claim }: { claim: ClaimProvenance }) {
  const [open, setOpen] = useState(false);
  const regionId = useId();
  return (
    <span className="citation-chip">
      <button
        type="button"
        className="chip-toggle"
        aria-expanded={open}
        aria-controls={regionId}
        onClick={() => setOpen((current) => !current)}
      >
        {open ? "Hide source" : "Source"}
      </button>
      {open && (
        <span
          id={regionId}
          role="region"
          aria-label={`Citation: ${claim.predicate}`}
          className="chip-detail"
        >
          <ConfidenceBadge tier={claim.tier} />
          {claim.sources.map((source) =>
            source.url ? (
              <a key={source.source_id} href={source.url}>
                {source.label}
              </a>
            ) : (
              <span key={source.source_id}>{source.label}</span>
            ),
          )}
          <span className="hint">claim {claim.claim_id}</span>
        </span>
      )}
    </span>
  );
}
