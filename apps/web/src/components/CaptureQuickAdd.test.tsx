import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { SessionProvider } from "@/lib/session";

import { CaptureQuickAdd } from "./CaptureQuickAdd";

function jobResponse(status = "complete") {
  return {
    id: "job-1",
    job_type: "bulk_import",
    status,
    progress_percent: 100,
    items: [],
    items_created: { Note: 1 },
    created_at: new Date().toISOString(),
  };
}

function mount(onSuccess = vi.fn(), onClose = vi.fn(), token: string | null = "tok") {
  render(
    <SessionProvider initialToken={token}>
      <button>opener</button>
      <CaptureQuickAdd onClose={onClose} onSuccess={onSuccess} />
    </SessionProvider>,
  );
  return { onSuccess, onClose };
}

beforeEach(() => {
  vi.restoreAllMocks();
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response(JSON.stringify(jobResponse()), { status: 201 })),
  );
});

describe("CaptureQuickAdd (DESIGN_SYSTEM 4.2, ACCESSIBILITY 4.3)", () => {
  it("captures a note by keyboard alone and reports elapsed time under a minute", async () => {
    const user = userEvent.setup();
    const { onSuccess, onClose } = mount();

    await user.keyboard("{Tab}");
    await user.type(screen.getByLabelText("Note"), "a keyboard-captured thought");
    await user.click(screen.getByRole("button", { name: "Capture" }));

    await waitFor(() => expect(onSuccess).toHaveBeenCalled());
    const [job, elapsed] = onSuccess.mock.calls[0];
    expect(job.id).toBe("job-1");
    expect(elapsed).toBeLessThan(60);
    expect(onClose).toHaveBeenCalled();

    const form = (fetch as ReturnType<typeof vi.fn>).mock.calls[0][1].body as FormData;
    const payload = JSON.parse(form.get("payload") as string);
    expect(payload.notes[0].body).toBe("a keyboard-captured thought");
    expect(payload.notes[0].privacy_tier).toBe("P2");
  });

  it("sends the selected tier and shows the audience hint", async () => {
    const user = userEvent.setup();
    mount();
    await user.selectOptions(screen.getByLabelText("Privacy tier"), "P1");
    expect(screen.getByText(/Trusted: visible to granted collaborators/)).toBeVisible();
    await user.type(screen.getByLabelText("Note"), "shared");
    await user.click(screen.getByRole("button", { name: "Capture" }));
    await waitFor(() => expect(fetch).toHaveBeenCalled());
    const form = (fetch as ReturnType<typeof vi.fn>).mock.calls[0][1].body as FormData;
    expect(JSON.parse(form.get("payload") as string).notes[0].privacy_tier).toBe("P1");
  });

  it("captures a link as a note with link context", async () => {
    const user = userEvent.setup();
    mount();
    await user.click(screen.getByRole("tab", { name: "link" }));
    await user.type(screen.getByLabelText("Link"), "https://example.test/talk");
    await user.click(screen.getByRole("button", { name: "Capture" }));
    await waitFor(() => expect(fetch).toHaveBeenCalled());
    const payload = JSON.parse(
      ((fetch as ReturnType<typeof vi.fn>).mock.calls[0][1].body as FormData).get(
        "payload",
      ) as string,
    );
    expect(payload.notes[0].note_context).toBe("link");
    expect(payload.notes[0].body).toBe("https://example.test/talk");
  });

  it("uploads files with the chosen tier applied", async () => {
    const user = userEvent.setup();
    mount();
    await user.click(screen.getByRole("tab", { name: "file" }));
    const file = new File(["hello"], "hello.txt", { type: "text/plain" });
    await user.upload(screen.getByLabelText("Files"), file);
    await user.click(screen.getByRole("button", { name: "Capture" }));
    await waitFor(() => expect(fetch).toHaveBeenCalled());
    const form = (fetch as ReturnType<typeof vi.fn>).mock.calls[0][1].body as FormData;
    expect((form.get("files") as File).name).toBe("hello.txt");
    expect(JSON.parse(form.get("payload") as string).file_tiers["hello.txt"]).toBe("P2");
  });

  it("traps focus inside the dialog and closes on Escape restoring focus", async () => {
    const user = userEvent.setup();
    const { onClose } = mount();
    const dialog = screen.getByRole("dialog");
    const focusables = dialog.querySelectorAll<HTMLElement>("button, input, select, textarea");
    const last = focusables[focusables.length - 1];

    last.focus();
    await user.keyboard("{Tab}");
    expect(dialog.contains(document.activeElement)).toBe(true);

    focusables[0].focus();
    await user.keyboard("{Shift>}{Tab}{/Shift}");
    expect(dialog.contains(document.activeElement)).toBe(true);

    await user.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalled();
  });

  it("shows the error envelope message on failure and stays open", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({
              error: { code: "validation_failed", message: "Nothing to ingest.", request_id: "r" },
            }),
            { status: 422 },
          ),
      ),
    );
    const user = userEvent.setup();
    const { onSuccess } = mount();
    await user.type(screen.getByLabelText("Note"), "x");
    await user.click(screen.getByRole("button", { name: "Capture" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Nothing to ingest.");
    expect(onSuccess).not.toHaveBeenCalled();
  });

  it("asks for a session when no token is present", async () => {
    const user = userEvent.setup();
    const { onSuccess } = mount(vi.fn(), vi.fn(), null);
    await user.type(screen.getByLabelText("Note"), "x");
    await user.click(screen.getByRole("button", { name: "Capture" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("No session");
    expect(onSuccess).not.toHaveBeenCalled();
  });
});
