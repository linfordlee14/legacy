/**
 * API client for the /v1 surface (api/API_SPECIFICATION.md conventions:
 * bearer auth, error envelope, multipart ingestion creation).
 */

export type ApiErrorBody = {
  error: { code: string; message: string; request_id: string; details?: unknown };
};

export class ApiError extends Error {
  code: string;
  status: number;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

export type NoteInput = {
  title?: string;
  body: string;
  note_context?: string;
  privacy_tier?: string;
};

export type JobItem = {
  index: number;
  type: "note" | "file";
  name: string;
  status: string;
  reason?: string;
  artifact_id?: string;
  note_id?: string;
  duplicate_of?: string;
};

export type IngestionJob = {
  id: string;
  job_type: string;
  status: string;
  progress_percent: number | null;
  items: JobItem[];
  items_created: Record<string, number> | null;
  created_at: string;
};

export type PageOf<T> = { data: T[]; next_cursor: string | null };

const baseUrl = () => process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function parseError(response: Response): Promise<never> {
  let code = "internal";
  let message = "Request failed.";
  try {
    const body = (await response.json()) as ApiErrorBody;
    code = body.error.code;
    message = body.error.message;
  } catch {
    // fall through with defaults
  }
  throw new ApiError(response.status, code, message);
}

export async function createIngestionJob(
  token: string,
  input: { notes?: NoteInput[]; files?: File[]; fileTiers?: Record<string, string> },
): Promise<IngestionJob> {
  const form = new FormData();
  form.set(
    "payload",
    JSON.stringify({ notes: input.notes ?? [], file_tiers: input.fileTiers ?? {} }),
  );
  for (const file of input.files ?? []) {
    form.append("files", file, file.name);
  }
  const response = await fetch(`${baseUrl()}/v1/ingestion/jobs`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });
  if (!response.ok) await parseError(response);
  return (await response.json()) as IngestionJob;
}

export async function listIngestionJobs(
  token: string,
  cursor?: string | null,
): Promise<PageOf<IngestionJob>> {
  const params = new URLSearchParams();
  if (cursor) params.set("cursor", cursor);
  const query = params.size ? `?${params}` : "";
  const response = await fetch(`${baseUrl()}/v1/ingestion/jobs${query}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) await parseError(response);
  return (await response.json()) as PageOf<IngestionJob>;
}
