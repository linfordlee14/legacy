"use client";

/**
 * Persistent left navigation for the Private Workspace (UI_UX 4.1 and 4.2).
 * The step 12 shell surfaces the areas built so far; later areas (timeline,
 * graph, twin, journals, verification queue, agents) join as their steps land.
 */

import Link from "next/link";
import { usePathname } from "next/navigation";

const AREAS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/inbox", label: "Capture inbox" },
  { href: "/library", label: "Library" },
  { href: "/settings", label: "Settings" },
];

export function WorkspaceNav() {
  const pathname = usePathname();
  return (
    <nav aria-label="Workspace" className="workspace-nav">
      <p className="brand">Legacy</p>
      <ul>
        {AREAS.map((area) => {
          const active = pathname === area.href || pathname.startsWith(area.href + "/");
          return (
            <li key={area.href}>
              <Link href={area.href} aria-current={active ? "page" : undefined}>
                {area.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
