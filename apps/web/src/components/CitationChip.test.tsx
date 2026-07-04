import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { CitationChip } from "./CitationChip";

const CLAIM = {
  claim_id: "clm-7",
  tier: "verified",
  predicate: "presented_at",
  sources: [
    { source_id: "s1", label: "GDG Cape Town event page", url: "https://example.test/e" },
    { source_id: "s2", label: "MASTER_CONTEXT.md", url: null },
  ],
};

describe("CitationChip (UI_UX 4.4; ACCESSIBILITY 4.5)", () => {
  it("is in the tab order and expands via the disclosure pattern", async () => {
    const user = userEvent.setup();
    render(<CitationChip claim={CLAIM} />);

    const toggle = screen.getByRole("button", { name: "Source" });
    await user.tab();
    expect(toggle).toHaveFocus();
    expect(toggle).toHaveAttribute("aria-expanded", "false");

    await user.keyboard("{Enter}");
    expect(screen.getByRole("button", { name: "Hide source" })).toHaveAttribute(
      "aria-expanded",
      "true",
    );
  });

  it("reveals a described region linking source and tier", async () => {
    const user = userEvent.setup();
    render(<CitationChip claim={CLAIM} />);
    await user.click(screen.getByRole("button", { name: "Source" }));

    const region = screen.getByRole("region", { name: "Citation: presented_at" });
    expect(region).toBeInTheDocument();
    // Tier as a text-labeled badge (NFR-043), sources with and without URLs.
    expect(screen.getByText("Verified")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "GDG Cape Town event page" }),
    ).toHaveAttribute("href", "https://example.test/e");
    expect(screen.getByText("MASTER_CONTEXT.md")).toBeInTheDocument();
    expect(screen.getByText("claim clm-7")).toBeInTheDocument();
  });
});
