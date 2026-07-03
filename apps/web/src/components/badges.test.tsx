import { render, screen } from "@testing-library/react";

import { ConfidenceBadge, PrivacyTierIndicator } from "./badges";

describe("provenance and privacy badges (NFR-043, DESIGN_SYSTEM 4.2)", () => {
  it("labels every confidence tier in text, not color alone", () => {
    for (const [tier, label] of [
      ["verified", "Verified"],
      ["self_reported", "Self-reported"],
      ["flagged", "Flagged"],
    ]) {
      const { unmount } = render(<ConfidenceBadge tier={tier} />);
      const badge = screen.getByLabelText(`confidence: ${label}`);
      expect(badge).toHaveTextContent(label);
      unmount();
    }
  });

  it("labels every privacy tier with tier code and word", () => {
    for (const [tier, word] of [
      ["P0", "Public"],
      ["P1", "Trusted"],
      ["P2", "Private"],
      ["P3", "Sealed"],
    ]) {
      const { unmount } = render(<PrivacyTierIndicator tier={tier} />);
      const badge = screen.getByLabelText(`privacy: ${word}`);
      expect(badge).toHaveTextContent(tier);
      expect(badge).toHaveTextContent(word);
      unmount();
    }
  });
});
