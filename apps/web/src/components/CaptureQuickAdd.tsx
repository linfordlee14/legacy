"use client";

/**
 * CaptureQuickAdd (DESIGN_SYSTEM 4.2; UI_UX 4.4): the one-modal capture for
 * notes, files, and links. Focus-trapped, keyboard-complete, Escape closes
 * and returns focus to the opener (ACCESSIBILITY 4.3). Voice mode arrives
 * with the transcription pipeline (FR-ING-003).
 */

import { useCallback, useEffect, useRef, useState } from "react";

import { createIngestionJob } from "@/lib/api";
import type { IngestionJob } from "@/lib/api";
import { useSession } from "@/lib/session";

import { TierSelect } from "./TierSelect";

type Mode = "note" | "file" | "link";

export function CaptureQuickAdd({
  onClose,
  onSuccess,
}: {
  onClose: () => void;
  onSuccess: (job: IngestionJob, elapsedSeconds: number) => void;
}) {
  const { token } = useSession();
  const [mode, setMode] = useState<Mode>("note");
  const [tier, setTier] = useState("P2");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [url, setUrl] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const openedAt = useRef<number>(Date.now());
  const dialogRef = useRef<HTMLDivElement>(null);
  const openerRef = useRef<Element | null>(null);

  useEffect(() => {
    openerRef.current = document.activeElement;
    const first = dialogRef.current?.querySelector<HTMLElement>(
      "button, input, select, textarea",
    );
    first?.focus();
    return () => {
      (openerRef.current as HTMLElement | null)?.focus?.();
    };
  }, []);

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if (event.key === "Escape") {
        event.stopPropagation();
        onClose();
        return;
      }
      if (event.key !== "Tab") return;
      const focusables = Array.from(
        dialogRef.current?.querySelectorAll<HTMLElement>(
          'button, input, select, textarea, [tabindex]:not([tabindex="-1"])',
        ) ?? [],
      ).filter((element) => !element.hasAttribute("disabled"));
      if (focusables.length === 0) return;
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    },
    [onClose],
  );

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    if (!token) {
      setError("No session. Sign in first.");
      return;
    }
    setBusy(true);
    try {
      let job: IngestionJob;
      if (mode === "note") {
        job = await createIngestionJob(token, {
          notes: [{ title: title || undefined, body, privacy_tier: tier }],
        });
      } else if (mode === "link") {
        job = await createIngestionJob(token, {
          notes: [
            { title: title || undefined, body: url, note_context: "link", privacy_tier: tier },
          ],
        });
      } else {
        const fileTiers = Object.fromEntries(files.map((file) => [file.name, tier]));
        job = await createIngestionJob(token, { files, fileTiers });
      }
      onSuccess(job, (Date.now() - openedAt.current) / 1000);
      onClose();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Capture failed.");
    } finally {
      setBusy(false);
    }
  }

  const submittable =
    (mode === "note" && body.trim() !== "") ||
    (mode === "link" && url.trim() !== "") ||
    (mode === "file" && files.length > 0);

  return (
    <div className="modal-backdrop">
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="capture-title"
        className="modal"
        onKeyDown={handleKeyDown}
      >
        <h2 id="capture-title">Capture</h2>
        <div role="tablist" aria-label="Capture mode" className="mode-row">
          {(["note", "file", "link"] as Mode[]).map((candidate) => (
            <button
              key={candidate}
              role="tab"
              type="button"
              aria-selected={mode === candidate}
              onClick={() => setMode(candidate)}
            >
              {candidate}
            </button>
          ))}
        </div>

        <form onSubmit={submit}>
          {mode !== "file" && (
            <div className="field">
              <label htmlFor="capture-title-input">Title (optional)</label>
              <input
                id="capture-title-input"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
              />
            </div>
          )}
          {mode === "note" && (
            <div className="field">
              <label htmlFor="capture-body">Note</label>
              <textarea
                id="capture-body"
                required
                rows={5}
                value={body}
                onChange={(event) => setBody(event.target.value)}
              />
            </div>
          )}
          {mode === "link" && (
            <div className="field">
              <label htmlFor="capture-url">Link</label>
              <input
                id="capture-url"
                type="url"
                required
                value={url}
                onChange={(event) => setUrl(event.target.value)}
              />
            </div>
          )}
          {mode === "file" && (
            <div className="field">
              <label htmlFor="capture-files">Files</label>
              <input
                id="capture-files"
                type="file"
                multiple
                onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
              />
            </div>
          )}

          <TierSelect value={tier} onChange={setTier} />

          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}

          <div className="actions">
            <button type="button" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" disabled={busy || !submittable}>
              {busy ? "Capturing" : "Capture"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
