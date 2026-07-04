import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { SearchShortcut } from "./SearchShortcut";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

beforeEach(() => {
  push.mockClear();
  window.localStorage.clear();
});

describe("SearchShortcut (UI_UX 4.2; ACCESSIBILITY 4.3)", () => {
  it("routes to search on / from anywhere outside inputs", () => {
    render(<SearchShortcut />);
    fireEvent.keyDown(document.body, { key: "/" });
    expect(push).toHaveBeenCalledWith("/search");
  });

  it("never fires while typing in a field", () => {
    render(
      <>
        <SearchShortcut />
        <label>
          Note <textarea defaultValue="" />
        </label>
      </>,
    );
    fireEvent.keyDown(screen.getByLabelText("Note"), { key: "/" });
    expect(push).not.toHaveBeenCalled();
  });

  it("is disableable per the shortcut policy", () => {
    window.localStorage.setItem("legacy.shortcut.search", "off");
    render(<SearchShortcut />);
    fireEvent.keyDown(document.body, { key: "/" });
    expect(push).not.toHaveBeenCalled();
  });
});
