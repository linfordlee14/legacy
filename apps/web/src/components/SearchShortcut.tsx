"use client";

/**
 * Global search shortcut (UI_UX 4.2: `/` from any workspace screen).
 * Never fires while typing and can be disabled (ACCESSIBILITY 4.3) via
 * localStorage["legacy.shortcut.search"] = "off". On the search screen
 * itself it re-focuses the query input via the legacy:search-focus event.
 */

import { useRouter } from "next/navigation";
import { useEffect } from "react";

function isEditable(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  return (
    ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName) || target.isContentEditable
  );
}

export function SearchShortcut() {
  const router = useRouter();
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key !== "/" || event.metaKey || event.ctrlKey || event.altKey) return;
      if (isEditable(event.target)) return;
      if (window.localStorage.getItem("legacy.shortcut.search") === "off") return;
      event.preventDefault();
      router.push("/search");
      window.dispatchEvent(new CustomEvent("legacy:search-focus"));
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [router]);
  return null;
}
