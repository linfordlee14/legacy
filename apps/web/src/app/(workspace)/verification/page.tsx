"use client";

/**
 * Verification queue screen (MVP-020; FS-009; UI_UX 4.3 queue mock).
 * Lists open Flagged and stale Self-reported claims with their evidence,
 * lets the owner attach evidence Sources, and resolves tier decisions
 * with a plain-language explanation of what each tier means
 * (ACCESSIBILITY 4.4). Nothing resolves automatically: every decision is
 * an explicit owner action, and the API enforces step-up, the policy
 * service, and the database tier guard behind this screen.
 */

import { useCallback, useEffect, useState } from "react";

import { ConfidenceBadge, PrivacyTierIndicator } from "@/components/badges";
import { ApiError } from "@/lib/api";
import {
  attachEvidence,
  getQueue,
  resolveClaim,
  type Queue,
  type QueueClaim,
} from "@/lib/verification";
import { useSession } from "@/lib/session";

const TIER_MEANING: Record<string, string> = {
  verified:
    "Verified means you reviewed supporting evidence; the statement may be asserted as fact wherever it appears.",
  self_reported:
    "Self-reported means the statement stays attributed to Linford and is never asserted as established fact.",
  flagged:
    "Flagged keeps the statement in the queue as unverified; surfaces either omit it or mark it explicitly unverified.",
};

function EvidenceForm({
  claim,
  onDone,
}: {
  claim: QueueClaim;
  onDone: (updated: QueueClaim) => void;
}) {
  const { token } = useSession();
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [url, setUrl] = useState("");
  const [sourceType, setSourceType] = useState("url");
  const [supportType, setSupportType] = useState<"supports" | "contradicts">("supports");
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const updated = await attachEvidence(
        claim.id,
        {
          support_type: supportType,
          note: note || undefined,
          source: {
            source_type: sourceType,
            title,
            url: url || undefined,
          },
        },
        token,
      );
      setOpen(false);
      setTitle("");
      setUrl("");
      setNote("");
      onDone(updated);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not attach evidence.");
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <button type="button" aria-expanded={false} onClick={() => setOpen(true)}>
        Attach evidence
      </button>
    );
  }
  return (
    <form onSubmit={submit} className="evidence-form" aria-label="Attach evidence">
      <label>
        Source title
        <input value={title} onChange={(e) => setTitle(e.target.value)} required />
      </label>
      <label>
        Source URL (optional)
        <input value={url} onChange={(e) => setUrl(e.target.value)} type="url" />
      </label>
      <label>
        Source type
        <select value={sourceType} onChange={(e) => setSourceType(e.target.value)}>
          <option value="url">Web page</option>
          <option value="document">Document</option>
          <option value="testimony">Testimony</option>
        </select>
      </label>
      <fieldset>
        <legend>This evidence</legend>
        <label>
          <input
            type="radio"
            name={`support-${claim.id}`}
            checked={supportType === "supports"}
            onChange={() => setSupportType("supports")}
          />
          supports the claim
        </label>
        <label>
          <input
            type="radio"
            name={`support-${claim.id}`}
            checked={supportType === "contradicts"}
            onChange={() => setSupportType("contradicts")}
          />
          contradicts the claim
        </label>
      </fieldset>
      <label>
        Note (optional)
        <input value={note} onChange={(e) => setNote(e.target.value)} />
      </label>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      <div className="search-row">
        <button type="submit" disabled={busy || !title.trim()}>
          Attach
        </button>
        <button type="button" onClick={() => setOpen(false)}>
          Cancel
        </button>
      </div>
    </form>
  );
}

function ResolveForm({
  claim,
  onDone,
}: {
  claim: QueueClaim;
  onDone: (outcome: string, updated: QueueClaim) => void;
}) {
  const { token } = useSession();
  const [open, setOpen] = useState(false);
  const [target, setTarget] = useState<"verified" | "self_reported" | "reject">("verified");
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const result = await resolveClaim(
        claim.id,
        target === "reject"
          ? { decision: "reject", note: note || undefined }
          : { decision: "apply", target_tier: target, note: note || undefined },
        token,
      );
      setOpen(false);
      onDone(result.outcome, result.claim);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not resolve the claim.");
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <button type="button" aria-expanded={false} onClick={() => setOpen(true)}>
        Resolve…
      </button>
    );
  }
  const meaning =
    target === "reject" ? TIER_MEANING[claim.confidence_tier] : TIER_MEANING[target];
  return (
    <form onSubmit={submit} className="resolve-form" aria-label="Resolve claim">
      <fieldset>
        <legend>Decision</legend>
        <label>
          <input
            type="radio"
            name={`resolve-${claim.id}`}
            checked={target === "verified"}
            onChange={() => setTarget("verified")}
          />
          Mark verified (requires supporting evidence)
        </label>
        <label>
          <input
            type="radio"
            name={`resolve-${claim.id}`}
            checked={target === "self_reported"}
            onChange={() => setTarget("self_reported")}
          />
          Mark self-reported
        </label>
        <label>
          <input
            type="radio"
            name={`resolve-${claim.id}`}
            checked={target === "reject"}
            onChange={() => setTarget("reject")}
          />
          Keep as is (reviewed)
        </label>
      </fieldset>
      <p className="hint">{meaning}</p>
      <label>
        Decision note (optional)
        <input value={note} onChange={(e) => setNote(e.target.value)} />
      </label>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      <div className="search-row">
        <button type="submit" disabled={busy}>
          Apply decision
        </button>
        <button type="button" onClick={() => setOpen(false)}>
          Cancel
        </button>
      </div>
    </form>
  );
}

export default function VerificationQueuePage() {
  const { token } = useSession();
  const [queue, setQueue] = useState<Queue | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [announce, setAnnounce] = useState("");

  const load = useCallback(async () => {
    try {
      setQueue(await getQueue(token));
      setError(null);
    } catch (caught) {
      setError(
        caught instanceof ApiError ? caught.message : "Could not load the verification queue.",
      );
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  function replaceClaim(updated: QueueClaim) {
    setQueue((current) =>
      current
        ? { ...current, items: current.items.map((c) => (c.id === updated.id ? updated : c)) }
        : current,
    );
  }

  function onResolved(outcome: string, updated: QueueClaim) {
    if (outcome === "applied") {
      setAnnounce(`Claim resolved to ${updated.confidence_tier}.`);
      void load();
    } else {
      setAnnounce("Claim reviewed and kept at its tier.");
      replaceClaim(updated);
    }
  }

  return (
    <section aria-labelledby="vq-heading">
      <h1 id="vq-heading">
        Verification queue{queue ? ` (${queue.items.length})` : ""}
      </h1>
      <p className="hint">
        Claims here are unverified or due for review. A tier decision changes how the
        statement is presented everywhere; nothing is ever upgraded automatically.
      </p>

      <p role="status" aria-live="polite" className="search-status">
        {announce}
      </p>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}

      {queue && queue.items.length === 0 && (
        <p>The queue is empty. Every claim is verified or awaiting its review date.</p>
      )}

      <ul className="queue-list" aria-label="Claims awaiting verification">
        {queue?.items.map((claim) => (
          <li key={claim.id} className="queue-item">
            <article aria-label={claim.statement}>
              <div className="detail-header">
                <ConfidenceBadge tier={claim.confidence_tier} />
                <PrivacyTierIndicator tier={claim.privacy_tier} />
                <span className="hint">{claim.predicate}</span>
              </div>
              <p className="statement">{claim.statement}</p>
              {claim.tier_rationale && <p className="hint">{claim.tier_rationale}</p>}
              <p className="hint">
                evidence: {claim.supporting_count} supporting,{" "}
                {claim.contradicting_count} contradicting
              </p>
              {claim.evidence.length > 0 && (
                <ul className="evidence-list">
                  {claim.evidence.map((evidence) => (
                    <li key={`${evidence.source_id}-${evidence.support_type}`}>
                      {evidence.support_type}:{" "}
                      {evidence.url ? (
                        <a href={evidence.url}>{evidence.title}</a>
                      ) : (
                        evidence.title
                      )}
                      {evidence.note ? ` · ${evidence.note}` : ""}
                    </li>
                  ))}
                </ul>
              )}
              <div className="search-row">
                <EvidenceForm claim={claim} onDone={replaceClaim} />
                <ResolveForm claim={claim} onDone={onResolved} />
              </div>
            </article>
          </li>
        ))}
      </ul>
    </section>
  );
}
