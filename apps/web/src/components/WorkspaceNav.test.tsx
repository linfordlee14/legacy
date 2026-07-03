import { render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { WorkspaceNav } from "./WorkspaceNav";

const mockPathname = vi.fn();
vi.mock("next/navigation", () => ({ usePathname: () => mockPathname() }));

describe("WorkspaceNav (UI_UX 4.1 and 4.2)", () => {
  it("exposes all shipped areas as a labeled navigation landmark", () => {
    mockPathname.mockReturnValue("/dashboard");
    render(<WorkspaceNav />);
    const nav = screen.getByRole("navigation", { name: "Workspace" });
    for (const label of ["Dashboard", "Capture inbox", "Library", "Settings"]) {
      expect(screen.getByRole("link", { name: label })).toBeInTheDocument();
    }
    expect(nav).toBeInTheDocument();
  });

  it("marks the active area with aria-current, including nested routes", () => {
    mockPathname.mockReturnValue("/library/notes/abc");
    render(<WorkspaceNav />);
    expect(screen.getByRole("link", { name: "Library" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: "Dashboard" })).not.toHaveAttribute(
      "aria-current",
    );
  });
});
