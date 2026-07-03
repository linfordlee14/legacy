"use client";

/**
 * Global capture affordance (UI_UX 4.2 and 4.4): the fixed capture button
 * and the `c` shortcut on every screen. The shortcut never fires while
 * typing and can be disabled (ACCESSIBILITY 4.3) via
 * localStorage["legacy.shortcut.capture"] = "off".
 */

import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";

import type { IngestionJob } from "@/lib/api";

import { CaptureQuickAdd } from "./CaptureQuickAdd";

function isEditable(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  return (
    ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName) || target.isContentEditable
  );
}

export function CaptureProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key !== "c" || event.metaKey || event.ctrlKey || event.altKey) return;
      if (isEditable(event.target)) return;
      if (window.localStorage.getItem("legacy.shortcut.capture") === "off") return;
      event.preventDefault();
      setOpen(true);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const handleSuccess = useCallback((job: IngestionJob, elapsedSeconds: number) => {
    const seconds = elapsedSeconds.toFixed(1);
    setToast(`Captured in ${seconds}s (job ${job.status})`);
    window.dispatchEvent(new CustomEvent("legacy:capture", { detail: job }));
    window.setTimeout(() => setToast(null), 6000);
  }, []);

  return (
    <>
      {children}
      <button
        type="button"
        className="capture-button"
        aria-haspopup="dialog"
        onClick={() => setOpen(true)}
      >
        + Capture
      </button>
      {open && (
        <CaptureQuickAdd onClose={() => setOpen(false)} onSuccess={handleSuccess} />
      )}
      <div aria-live="polite" className="toast-region">
        {toast && <p className="toast">{toast}</p>}
      </div>
    </>
  );
}
