"use client";

/**
 * Capture-time privacy tier selection (DESIGN_SYSTEM TierSelector, capture
 * variant): default P2, audience stated in text next to the control so the
 * consequence is always visible (UI_UX 4.4).
 */

const AUDIENCES: Record<string, string> = {
  P0: "Public: visible to everyone",
  P1: "Trusted: visible to granted collaborators",
  P2: "Private: only you",
  P3: "Sealed: locked until release conditions are met",
};

export function TierSelect({
  value,
  onChange,
  id = "capture-tier",
}: {
  value: string;
  onChange: (tier: string) => void;
  id?: string;
}) {
  return (
    <div className="field">
      <label htmlFor={id}>Privacy tier</label>
      <select id={id} value={value} onChange={(event) => onChange(event.target.value)}>
        {Object.keys(AUDIENCES).map((tier) => (
          <option key={tier} value={tier}>
            {tier}
          </option>
        ))}
      </select>
      <p className="hint" aria-live="polite">
        {AUDIENCES[value]}
      </p>
    </div>
  );
}
