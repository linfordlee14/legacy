"use client";

/**
 * Capture inbox (UI_UX 4.1): ingestion jobs with per-item statuses, review
 * flags surfaced first, and the 4.5 states (empty, loading, error). Refreshes
 * on every successful capture.
 */

import { useCallback, useEffect, useState } from "react";

import { listIngestionJobs } from "@/lib/api";
import type { IngestionJob } from "@/lib/api";
import { useSession } from "@/lib/session";

function JobRow({ job }: { job: IngestionJob }) {
  const review = job.status === "review" || job.status === "failed";
  return (
    <li className={review ? "job job-review" : "job"}>
      <p>
        <strong>{job.status}</strong> · {job.job_type} ·{" "}
        {new Date(job.created_at).toLocaleString()}
      </p>
      <ul>
        {job.items.map((item) => (
          <li key={item.index}>
            {item.name}: {item.status}
            {item.reason ? ` (${item.reason})` : ""}
          </li>
        ))}
      </ul>
    </li>
  );
}

function DevTokenGate() {
  const { setToken } = useSession();
  const [value, setValue] = useState("");
  if (process.env.NEXT_PUBLIC_LEGACY_ENV === "production") return null;
  return (
    <form
      className="dev-token"
      onSubmit={(event) => {
        event.preventDefault();
        setToken(value || null);
      }}
    >
      <label htmlFor="dev-token">
        Session token (development stand-in until the workspace shell signs in)
      </label>
      <input
        id="dev-token"
        value={value}
        onChange={(event) => setValue(event.target.value)}
      />
      <button type="submit">Use token</button>
    </form>
  );
}

export default function InboxPage() {
  const { token } = useSession();
  const [jobs, setJobs] = useState<IngestionJob[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const page = await listIngestionJobs(token);
      setJobs(page.data);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load the inbox.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void refresh();
    const onCapture = () => void refresh();
    window.addEventListener("legacy:capture", onCapture);
    return () => window.removeEventListener("legacy:capture", onCapture);
  }, [refresh]);

  return (
    <section className="inbox">
      <h1>Capture inbox</h1>
      {!token && (
        <>
          <p>Sign in to see your captures.</p>
          <DevTokenGate />
        </>
      )}
      {token && loading && jobs === null && <p aria-live="polite">Loading your captures.</p>}
      {token && error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {token && jobs !== null && jobs.length === 0 && !error && (
        <div className="empty-state">
          <h2>Nothing captured yet</h2>
          <p>
            Everything you add lands here first. Press the Capture button, or the c key,
            anywhere in the workspace.
          </p>
        </div>
      )}
      {token && jobs !== null && jobs.length > 0 && (
        <ul className="job-list">
          {[...jobs]
            .sort((a, b) => Number(b.status === "review") - Number(a.status === "review"))
            .map((job) => (
              <JobRow key={job.id} job={job} />
            ))}
        </ul>
      )}
    </section>
  );
}
