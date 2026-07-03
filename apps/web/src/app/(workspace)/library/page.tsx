"use client";

/**
 * Library (UI_UX 4.1 item list): notes and captured documents with privacy
 * indicators, and the 4.5 states.
 */

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { PrivacyTierIndicator } from "@/components/badges";
import { listContent } from "@/lib/content";
import type { ContentItem } from "@/lib/content";
import { useSession } from "@/lib/session";

type Collection = "notes" | "artifacts";

export default function LibraryPage() {
  const { token } = useSession();
  const [collection, setCollection] = useState<Collection>("notes");
  const [items, setItems] = useState<ContentItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const page = await listContent(collection, token);
      setItems(page.data);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load the library.");
    } finally {
      setLoading(false);
    }
  }, [collection, token]);

  useEffect(() => {
    void load();
    const onCapture = () => void load();
    window.addEventListener("legacy:capture", onCapture);
    return () => window.removeEventListener("legacy:capture", onCapture);
  }, [load]);

  return (
    <section>
      <h1>Library</h1>
      <div role="tablist" aria-label="Collection" className="mode-row">
        {(["notes", "artifacts"] as Collection[]).map((candidate) => (
          <button
            key={candidate}
            role="tab"
            type="button"
            aria-selected={collection === candidate}
            onClick={() => setCollection(candidate)}
          >
            {candidate === "notes" ? "Notes" : "Documents"}
          </button>
        ))}
      </div>

      {loading && items === null && <p aria-live="polite">Loading.</p>}
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {items !== null && items.length === 0 && !error && (
        <div className="empty-state">
          <h2>Nothing here yet</h2>
          <p>Captured {collection === "notes" ? "notes" : "documents"} will appear here.</p>
        </div>
      )}
      {items !== null && items.length > 0 && (
        <ul className="item-list">
          {items.map((item) => (
            <li key={item.id}>
              <Link href={`/library/${collection}/${item.id}`}>
                {item.title || (collection === "notes" ? "Untitled note" : "Untitled document")}
              </Link>
              <PrivacyTierIndicator tier={item.privacy_tier} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
