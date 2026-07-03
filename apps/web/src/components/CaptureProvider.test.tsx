import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { SessionProvider } from "@/lib/session";

import { CaptureProvider } from "./CaptureProvider";

function mount() {
  render(
    <SessionProvider initialToken="tok">
      <CaptureProvider>
        <input aria-label="somewhere to type" />
      </CaptureProvider>
    </SessionProvider>,
  );
}

beforeEach(() => {
  window.localStorage.clear();
});

describe("CaptureProvider (UI_UX 4.2 and 4.4; ACCESSIBILITY 4.3)", () => {
  it("renders the capture button on every screen", () => {
    mount();
    expect(screen.getByRole("button", { name: "+ Capture" })).toBeVisible();
  });

  it("opens the modal with the c shortcut", async () => {
    const user = userEvent.setup();
    mount();
    await user.keyboard("c");
    expect(screen.getByRole("dialog", { name: "Capture" })).toBeVisible();
  });

  it("does not fire the shortcut while typing", async () => {
    const user = userEvent.setup();
    mount();
    await user.click(screen.getByLabelText("somewhere to type"));
    await user.keyboard("c");
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("respects the shortcut disable flag", async () => {
    window.localStorage.setItem("legacy.shortcut.capture", "off");
    const user = userEvent.setup();
    mount();
    await user.keyboard("c");
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("announces the capture result with the measured time", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({
              id: "j1",
              job_type: "bulk_import",
              status: "complete",
              progress_percent: 100,
              items: [],
              items_created: { Note: 1 },
              created_at: new Date().toISOString(),
            }),
            { status: 201 },
          ),
      ),
    );
    const user = userEvent.setup();
    mount();
    await user.click(screen.getByRole("button", { name: "+ Capture" }));
    await user.type(screen.getByLabelText("Note"), "measured capture");
    await user.click(screen.getByRole("button", { name: "Capture" }));

    const toast = await screen.findByText(/Captured in \d+(\.\d+)?s/);
    const seconds = Number(/Captured in ([\d.]+)s/.exec(toast.textContent ?? "")?.[1]);
    expect(seconds).toBeLessThan(60);
  });
});
