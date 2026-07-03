"use client";

/**
 * Item detail (UI_UX 4.1): the content plus its privacy indicator and, where
 * claims exist, ConfidenceBadges over the provenance block. not_found renders
 * a plain message (the API does not distinguish missing from above-ceiling).
 */

import Link from "next/link";
import { notFound, useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { ConfidenceBadge, PrivacyTierIndicator } from "@/components/badges";
import { ApiError } from "@/lib/api";
import { getContent } from "@/lib/content";
import type { ContentItem } from "@/lib/content";
import { useSession } from "@/lib/session";

export default function ItemDetailPage() {
  const params = useParams<{ collection: string; id: string }>();
  const collection = params.collection === "artifacts" ? "artifacts" : "notes";
  const { token } = useSession();
  const [item, setItem] = useState<ContentItem | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [missing, setMissing] = useState(false);

  useEffect(() => {
    let active = true;
    getContent(collection, params.id, token)
      .then((result) => active && setItem(result))
      .catch((caught) => {
        if (!active) return;
        if (caught instanceof ApiError && caught.status === 404) {
          setMissing(true);
        } else {
          setError(caught instanceof Error ? caught.message : "Could not load this item.");
        }
      });
    return () => {
      active = false;
    };
  }, [collection, params.id, token]);

  if (missing) notFound();

  if (error) {
    return (
      <section>
        <p role="alert" className="error">
          {error}
        </p>
      </section>
    );
  }

  if (!item) {
    return (
      <section>
        <p aria-live="polite">Loading.</p>
      </section>
    );
  }

  const content = collection === "notes" ? item.body : item.canonical_markdown;
  const claims = item.provenance?.claims ?? [];

  return (
    <section>
      <p>
        <Link href="/library">Back to library</Link>
      </p>
      <div className="detail-header">
        <h1>{item.title || (collection === "notes" ? "Untitled note" : "Untitled document")}</h1>
        <PrivacyTierIndicator tier={item.privacy_tier} />
      </div>
      {collection === "artifacts" && (
        <p className="hint">
          {item.artifact_type} · extraction: {item.extraction_status}
        </p>
      )}
      {content ? (
        <pre className="content-body">{content}</pre>
      ) : (
        <p className="hint">No extracted text for this item.</p>
      )}

      {claims.length > 0 && (
        <section aria-label="Provenance" className="provenance">
          <h2>Claims about this item</h2>
          <ul>
            {claims.map((claim) => (
              <li key={claim.claim_id}>
                <ConfidenceBadge tier={claim.tier} /> {claim.predicate}
                {claim.sources.length > 0 && (
                  <span className="hint">
                    {" "}
                    · {claim.sources.map((source) => source.label).join(", ")}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}
    </section>
  );
}
