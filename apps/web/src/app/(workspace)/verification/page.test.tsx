import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { SessionProvider } from "@/lib/session";

import VerificationQueuePage from "./page";

function queueClaim(overrides: Record<string, unknown> = {}) {
  return {
    id: "clm-1",
    subject_type: "Project",
    subject_id: "prj-1",
    predicate: "placed_at",
    statement: "SpazaLink reportedly placed 3rd at SA Startup Week 2026.",
    confidence_tier: "flagged",
    tier_rationale: "Placement explicitly flagged for verification.",
    verified_at: null,
    review_due_at: null,
    privacy_tier: "P2",
    evidence: [
      {
        source_id: "src-1",
        source_type: "document",
        title: "MASTER_CONTEXT.md",
        url: null,
        publisher: null,
        reliability_note: null,
        support_type: "mentions",
        note: null,
      },
    ],
    supporting_count: 0,
    contradicting_count: 0,
    ...overrides,
  };
}

function stubFetch(handler: (url: string, init?: RequestInit) => unknown) {
  const mock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const result = handler(String(input), init);
    const [body, status] = Array.isArray(result) ? result : [result, 200];
    return new Response(JSON.stringify(body), { status: status as number });
  });
  vi.stubGlobal("fetch", mock);
  return mock;
}

function mount() {
  render(
    <SessionProvider initialToken="tok">
      <VerificationQueuePage />
    </SessionProvider>,
  );
}

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("VerificationQueuePage (MVP-020; FS-009; NFR-043)", () => {
  it("lists queue items with text-labeled badges, evidence, and rationale", async () => {
    stubFetch(() => ({ items: [queueClaim()], open_flagged: 1, stale_self_reported: 0 }));
    mount();

    expect(
      await screen.findByRole("heading", { name: "Verification queue (1)" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Flagged")).toBeInTheDocument(); // never emoji alone
    expect(screen.getByText("P2 Private")).toBeInTheDocument();
    expect(
      screen.getByText("SpazaLink reportedly placed 3rd at SA Startup Week 2026."),
    ).toBeInTheDocument();
    expect(screen.getByText(/0 supporting, 0 contradicting/)).toBeInTheDocument();
    expect(screen.getByText(/mentions: MASTER_CONTEXT.md/)).toBeInTheDocument();
  });

  it("attaches evidence through the disclosure form", async () => {
    const updated = queueClaim({ supporting_count: 1 });
    const mock = stubFetch((url, init) => {
      if (url.includes("/evidence") && init?.method === "POST") return [updated, 201];
      return { items: [queueClaim()], open_flagged: 1, stale_self_reported: 0 };
    });
    const user = userEvent.setup();
    mount();

    await user.click(await screen.findByRole("button", { name: "Attach evidence" }));
    await user.type(screen.getByLabelText("Source title"), "Official results page");
    await user.click(screen.getByLabelText("supports the claim"));
    await user.click(screen.getByRole("button", { name: "Attach" }));

    await waitFor(() => expect(screen.getByText(/1 supporting/)).toBeInTheDocument());
    const call = mock.mock.calls.find(([url]) => String(url).includes("/evidence"));
    const payload = JSON.parse(String(call?.[1]?.body));
    expect(payload.support_type).toBe("supports");
    expect(payload.source.title).toBe("Official results page");
  });

  it("resolves with a plain-language explanation of the chosen tier", async () => {
    const verified = queueClaim({ confidence_tier: "verified", verified_at: "2026-07-04" });
    const mock = stubFetch((url, init) => {
      if (url.includes("/resolve") && init?.method === "POST") {
        return { outcome: "applied", claim: verified };
      }
      return { items: [queueClaim()], open_flagged: 1, stale_self_reported: 0 };
    });
    const user = userEvent.setup();
    mount();

    await user.click(await screen.findByRole("button", { name: "Resolve…" }));
    // The consequence of the decision is explained in plain language.
    expect(
      screen.getByText(/Verified means you reviewed supporting evidence/),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Apply decision" }));

    await waitFor(() => {
      const call = mock.mock.calls.find(([url]) => String(url).includes("/resolve"));
      expect(call).toBeTruthy();
      const payload = JSON.parse(String(call?.[1]?.body));
      expect(payload).toMatchObject({ decision: "apply", target_tier: "verified" });
    });
    expect(await screen.findByRole("status")).toHaveTextContent(
      "Claim resolved to verified.",
    );
  });

  it("surfaces a guard refusal as an alert without changing the queue", async () => {
    stubFetch((url, init) => {
      if (url.includes("/resolve") && init?.method === "POST") {
        return [
          {
            error: {
              code: "conflict",
              message: "The claim tier guard refused this resolution.",
              request_id: "r",
              details: { reason: "verification requires a supporting ClaimSource" },
            },
          },
          409,
        ];
      }
      return { items: [queueClaim()], open_flagged: 1, stale_self_reported: 0 };
    });
    const user = userEvent.setup();
    mount();

    await user.click(await screen.findByRole("button", { name: "Resolve…" }));
    await user.click(screen.getByRole("button", { name: "Apply decision" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /supporting ClaimSource/,
    );
    expect(screen.getByText("Flagged")).toBeInTheDocument();
  });

  it("shows the empty state when the queue is clear", async () => {
    stubFetch(() => ({ items: [], open_flagged: 0, stale_self_reported: 0 }));
    mount();
    expect(await screen.findByText(/The queue is empty/)).toBeInTheDocument();
  });
});
