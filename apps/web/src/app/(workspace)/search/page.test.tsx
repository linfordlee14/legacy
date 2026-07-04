import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { SessionProvider } from "@/lib/session";

import SearchPage from "./page";

function searchResponse(overrides: Record<string, unknown> = {}) {
  return {
    query: "zebra",
    mode: "hybrid",
    degraded: false,
    truncated: false,
    results: [
      {
        chunk_id: "ch1",
        chunk_ref: "e1#c0",
        entity_type: "Note",
        entity_id: "e1",
        title: "Public zebra",
        snippet: "The zebra fact everyone may read.",
        heading_path: "Projects > WildGuard",
        privacy_tier: "P2",
        score: 0.03,
        matched: ["lexical", "semantic"],
        provenance: {
          claims: [
            {
              claim_id: "clm1",
              tier: "self_reported",
              predicate: "is_described_as",
              sources: [{ source_id: "s1", label: "MASTER_CONTEXT.md", url: null }],
            },
          ],
        },
      },
    ],
    retrieval: { chunks_considered: 1, chunks_returned: 1, tier_ceiling: "P3" },
    ...overrides,
  };
}

function stubSearch(payload: unknown, status = 200) {
  const mock = vi.fn(
    async (_input: RequestInfo | URL) =>
      new Response(JSON.stringify(payload), { status }),
  );
  vi.stubGlobal("fetch", mock);
  return mock;
}

function mount() {
  render(
    <SessionProvider initialToken="tok">
      <SearchPage />
    </SessionProvider>,
  );
}

async function runSearch(user: ReturnType<typeof userEvent.setup>, q = "zebra") {
  await user.type(screen.getByLabelText("Search your records"), q);
  await user.click(screen.getByRole("button", { name: "Search" }));
}

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("SearchPage (MVP-018; FS-004; NFR-043; ACCESSIBILITY 4.3/4.5)", () => {
  it("searches by keyboard alone and renders result rows with badges and locators", async () => {
    const mock = stubSearch(searchResponse());
    const user = userEvent.setup();
    mount();

    await runSearch(user);

    const link = await screen.findByRole("link", { name: "Public zebra" });
    expect(link).toHaveAttribute("href", "/library/notes/e1");
    // Privacy tier and confidence carried by text labels, never color alone.
    expect(screen.getByText("P2 Private")).toBeInTheDocument();
    expect(screen.getByText("Self-reported")).toBeInTheDocument();
    expect(screen.getByText("Projects > WildGuard")).toBeInTheDocument();
    expect(screen.getByText(/keyword match \+ semantic match/)).toBeInTheDocument();

    const url = String(mock.mock.calls[0][0]);
    expect(url).toContain("/v1/search?");
    expect(url).toContain("q=zebra");
    expect(url).toContain("mode=hybrid");
  });

  it("highlights query terms in snippets", async () => {
    stubSearch(searchResponse());
    const user = userEvent.setup();
    mount();
    await runSearch(user);
    const marks = await screen.findAllByText("zebra", { selector: "mark" });
    expect(marks.length).toBeGreaterThan(0);
  });

  it("announces the outcome through a polite status region", async () => {
    stubSearch(searchResponse());
    const user = userEvent.setup();
    mount();
    await runSearch(user);
    await waitFor(() =>
      expect(screen.getByRole("status", { name: "" })).toHaveTextContent(
        '1 result for "zebra" (hybrid).',
      ),
    );
  });

  it("offers hybrid, keyword, and semantic modes and re-runs on change", async () => {
    const mock = stubSearch(searchResponse());
    const user = userEvent.setup();
    mount();

    expect(screen.getByRole("group", { name: "Search mode" })).toBeInTheDocument();
    await runSearch(user);
    await screen.findByRole("link", { name: "Public zebra" });

    await user.click(screen.getByRole("radio", { name: /Keyword/ }));
    await waitFor(() => expect(mock).toHaveBeenCalledTimes(2));
    expect(String(mock.mock.calls[1][0])).toContain("mode=lexical");
  });

  it("shows the degraded indicator exactly when the API reports it", async () => {
    stubSearch(searchResponse({ degraded: true }));
    const user = userEvent.setup();
    mount();
    await runSearch(user);
    expect(
      await screen.findByText(/Semantic ranking is unavailable right now/),
    ).toBeInTheDocument();
  });

  it("notes truncation of very long queries", async () => {
    stubSearch(searchResponse({ truncated: true }));
    const user = userEvent.setup();
    mount();
    await runSearch(user);
    expect(await screen.findByText(/shortened before searching/)).toBeInTheDocument();
  });

  it("renders a zero-result state that suggests without fabricating", async () => {
    stubSearch(searchResponse({ results: [] }));
    const user = userEvent.setup();
    mount();
    await runSearch(user, "quixotic theremin");
    expect(
      await screen.findByText(/No results in your records for/),
    ).toBeInTheDocument();
    expect(screen.getByText(/Nothing is ever invented/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "library" })).toBeInTheDocument();
  });

  it("surfaces API errors as an alert", async () => {
    stubSearch(
      { error: { code: "rate_limited", message: "Too many requests.", request_id: "r" } },
      429,
    );
    const user = userEvent.setup();
    mount();
    await runSearch(user);
    expect(await screen.findByRole("alert")).toHaveTextContent("Too many requests.");
  });

  it("focuses the query input on mount and on the search-focus event", async () => {
    stubSearch(searchResponse());
    mount();
    const input = screen.getByLabelText("Search your records");
    expect(input).toHaveFocus();
    input.blur();
    window.dispatchEvent(new CustomEvent("legacy:search-focus"));
    expect(input).toHaveFocus();
  });
});
