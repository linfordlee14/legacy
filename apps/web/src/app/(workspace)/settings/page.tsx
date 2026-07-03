"use client";

/**
 * Settings (UI_UX 4.1): session, the capture shortcut toggle (ACCESSIBILITY
 * 4.3 disable option), and appearance note. The dev-only session field stands
 * in until the shell binds real OIDC sign-in.
 */

import { useEffect, useState } from "react";

import { useSession } from "@/lib/session";

export default function SettingsPage() {
  const { token, setToken } = useSession();
  const [tokenInput, setTokenInput] = useState("");
  const [shortcutEnabled, setShortcutEnabled] = useState(true);

  useEffect(() => {
    setShortcutEnabled(
      window.localStorage.getItem("legacy.shortcut.capture") !== "off",
    );
  }, []);

  function toggleShortcut(next: boolean) {
    setShortcutEnabled(next);
    window.localStorage.setItem("legacy.shortcut.capture", next ? "on" : "off");
  }

  const isProduction = process.env.NEXT_PUBLIC_LEGACY_ENV === "production";

  return (
    <section>
      <h1>Settings</h1>

      <article className="panel">
        <h2>Session</h2>
        <p>{token ? "Signed in." : "Not signed in."}</p>
        {token ? (
          <button type="button" onClick={() => setToken(null)}>
            Sign out
          </button>
        ) : isProduction ? (
          <p>Sign-in binds here once the OIDC provider is configured.</p>
        ) : (
          <form
            onSubmit={(event) => {
              event.preventDefault();
              setToken(tokenInput || null);
            }}
          >
            <div className="field">
              <label htmlFor="settings-token">
                Session token (development stand-in for OIDC sign-in)
              </label>
              <input
                id="settings-token"
                value={tokenInput}
                onChange={(event) => setTokenInput(event.target.value)}
              />
            </div>
            <button type="submit">Use token</button>
          </form>
        )}
      </article>

      <article className="panel">
        <h2>Capture shortcut</h2>
        <label>
          <input
            type="checkbox"
            checked={shortcutEnabled}
            onChange={(event) => toggleShortcut(event.target.checked)}
          />{" "}
          Enable the c keyboard shortcut for capture
        </label>
      </article>

      <article className="panel">
        <h2>Appearance</h2>
        <p className="hint">
          Light and dark follow your system preference. Brand colors and
          typography are set once the owner defines them.
        </p>
      </article>
    </section>
  );
}
