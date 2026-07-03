"use client";

/**
 * Dashboard v0 (UI_UX 4.1): recent captures, ingestion job statuses, and a
 * review-flag count. The verification-queue and goal panels are placeholders
 * until their features land (F9, F14).
 */

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { listIngestionJobs } from "@/lib/api";
import type { IngestionJob } from "@/lib/api";
import { useSession } from "@/lib/session";

export default function DashboardPage() {
  const { token } = useSession();
  const [jobs, setJobs] = useState<IngestionJob[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!token) return;
    setError(null);
    try {
      const page = await listIngestionJobs(token);
      setJobs(page.data);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load the dashboard.");
    }
  }, [token]);

  useEffect(() => {
    void refresh();
    const onCapture = () => void refresh();
    window.addEventListener("legacy:capture", onCapture);
    return () => window.removeEventListener("legacy:capture", onCapture);
  }, [refresh]);

  const reviewCount = (jobs ?? []).filter(
    (job) => job.status === "review" || job.status === "failed",
  ).length;
  const recent = (jobs ?? []).slice(0, 5);

  return (
    <section>
      <h1>Dashboard</h1>
      {!token && <p>Sign in from Settings to see your workspace.</p>}
      {token && error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {token && (
        <div className="panel-grid">
          <article className="panel">
            <h2>Recent captures</h2>
            {recent.length === 0 ? (
              <p>Nothing yet. Press c to capture.</p>
            ) : (
              <ul>
                {recent.map((job) => (
                  <li key={job.id}>
                    {job.status} · {new Date(job.created_at).toLocaleString()}
                  </li>
                ))}
              </ul>
            )}
            <p>
              <Link href="/inbox">Open the capture inbox</Link>
            </p>
          </article>

          <article className="panel">
            <h2>Needs review</h2>
            <p className="count" aria-live="polite">
              {reviewCount}
            </p>
            <p>Ingestion items flagged for a decision.</p>
          </article>

          <article className="panel">
            <h2>Verification queue</h2>
            <p>Arrives with the verification engine (F9).</p>
          </article>
        </div>
      )}
    </section>
  );
}
