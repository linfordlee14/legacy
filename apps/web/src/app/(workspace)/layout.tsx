import type { ReactNode } from "react";

import { WorkspaceNav } from "@/components/WorkspaceNav";

/**
 * Workspace shell (UI_UX 4.1 and 4.2): skip link, persistent left navigation,
 * and the main content region. Capture (button and c shortcut) is provided
 * globally by the root layout.
 */
export default function WorkspaceLayout({ children }: { children: ReactNode }) {
  return (
    <div className="workspace">
      <a href="#workspace-main" className="skip-link">
        Skip to content
      </a>
      <WorkspaceNav />
      <div id="workspace-main" className="workspace-main">
        {children}
      </div>
    </div>
  );
}
