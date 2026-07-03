/**
 * Provenance and privacy indicators (DESIGN_SYSTEM 4.2, ACCESSIBILITY 4.5):
 * meaning is carried by a text label, never color or emoji alone (NFR-043).
 */

const TIER_LABEL: Record<string, string> = {
  verified: "Verified",
  self_reported: "Self-reported",
  flagged: "Flagged",
};

const PRIVACY_LABEL: Record<string, string> = {
  P0: "Public",
  P1: "Trusted",
  P2: "Private",
  P3: "Sealed",
};

export function ConfidenceBadge({ tier }: { tier: string }) {
  const label = TIER_LABEL[tier] ?? tier;
  return (
    <span className={`badge confidence confidence-${tier}`} aria-label={`confidence: ${label}`}>
      {label}
    </span>
  );
}

export function PrivacyTierIndicator({ tier }: { tier: string }) {
  const label = PRIVACY_LABEL[tier] ?? tier;
  return (
    <span className={`badge privacy privacy-${tier}`} aria-label={`privacy: ${label}`}>
      {tier} {label}
    </span>
  );
}
