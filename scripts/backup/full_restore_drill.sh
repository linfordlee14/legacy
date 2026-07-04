#!/usr/bin/env bash
# Full platform restore drill (BACKUP_AND_RECOVERY 4.6 runbook 3 plus the
# runbook 5 post-restore verification; MVP-021 acceptance).
#
# Backs up database AND object storage, restores both onto fresh scratch
# infrastructure, checks configuration (schema version) and re-derived
# indexes, verifies row counts, sampled content reads, and audit-log
# continuity against the manifest, then boots the API on the restored
# state and smoke-tests it. Reuses backup.sh and restore.sh exactly; no
# parallel machinery.
#
# Env:
#   LEGACY_DRILL_SOURCE_URL          database to back up
#   LEGACY_DRILL_SCRATCH_URL         EMPTY scratch database
#   LEGACY_DRILL_SOURCE_STORAGE_DIR  object storage tree to back up
#   LEGACY_DRILL_SCRATCH_STORAGE_DIR restore target (default: temp dir)
#   LEGACY_BACKUP_PUBLIC_KEY_FILE / LEGACY_BACKUP_PRIVATE_KEY_FILE
#       Key pair; LEGACY_DRILL_GENERATE_KEYS=1 creates an ephemeral pair
#       (synthetic-data drills only; real drills use escrow keys).
#   LEGACY_DRILL_API_PORT            default 8125
#   LEGACY_DRILL_RTO_TARGET_S        provisional RTO gate (default 3600;
#                                    the NFR-052 budget is 72 hours)
set -euo pipefail

: "${LEGACY_DRILL_SOURCE_URL:?set LEGACY_DRILL_SOURCE_URL}"
: "${LEGACY_DRILL_SCRATCH_URL:?set LEGACY_DRILL_SCRATCH_URL}"
: "${LEGACY_DRILL_SOURCE_STORAGE_DIR:?set LEGACY_DRILL_SOURCE_STORAGE_DIR}"
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "${HERE}/../.." && pwd)"
PORT="${LEGACY_DRILL_API_PORT:-8125}"
RTO_TARGET="${LEGACY_DRILL_RTO_TARGET_S:-3600}"
STARTED="$(date +%s)"
WORK="$(mktemp -d)"
SCRATCH_STORAGE="${LEGACY_DRILL_SCRATCH_STORAGE_DIR:-${WORK}/storage}"
API_PID=""
cleanup() {
  [ -n "${API_PID}" ] && kill "${API_PID}" 2>/dev/null || true
  rm -rf "${WORK}"
}
trap cleanup EXIT

if [ "${LEGACY_DRILL_GENERATE_KEYS:-0}" = "1" ]; then
  echo "drill3: generating ephemeral key pair (synthetic data only)"
  openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 \
    -out "${WORK}/drill.key" 2>/dev/null
  openssl pkey -in "${WORK}/drill.key" -pubout -out "${WORK}/drill.pub"
  export LEGACY_BACKUP_PRIVATE_KEY_FILE="${WORK}/drill.key"
  export LEGACY_BACKUP_PUBLIC_KEY_FILE="${WORK}/drill.pub"
fi

echo "drill3: step 1 backup (database plus object storage)"
LEGACY_BACKUP_DATABASE_URL="${LEGACY_DRILL_SOURCE_URL}" \
LEGACY_BACKUP_STORAGE_DIR="${LEGACY_DRILL_SOURCE_STORAGE_DIR}" \
LEGACY_BACKUP_DIR="${WORK}/backups" "${HERE}/backup.sh"
BACKUP_DIR="$(ls -d "${WORK}/backups"/* | tail -1)"
test -f "${BACKUP_DIR}/storage.enc" || {
  echo "event=full_restore_drill outcome=fail reason=no_storage_in_backup" >&2
  exit 1
}

echo "drill3: step 2 restore onto fresh infrastructure"
LEGACY_RESTORE_STORAGE_DIR="${SCRATCH_STORAGE}" \
  "${HERE}/restore.sh" "${BACKUP_DIR}" "${LEGACY_DRILL_SCRATCH_URL}"

echo "drill3: step 3 configuration and index re-derivation checks"
MANIFEST_SCHEMA="$(python3 -c "import json;print(json.load(open('${BACKUP_DIR}/manifest.json'))['schema_version'])")"
SCRATCH_SCHEMA="$(psql "${LEGACY_DRILL_SCRATCH_URL}" -Atc 'SELECT version_num FROM alembic_version')"
if [ "${MANIFEST_SCHEMA}" != "${SCRATCH_SCHEMA}" ]; then
  echo "event=full_restore_drill outcome=fail reason=schema_mismatch manifest=${MANIFEST_SCHEMA} scratch=${SCRATCH_SCHEMA}" >&2
  exit 1
fi
for index in ix_embedding_chunk_ann_gemini_1536 ix_embedding_chunk_text_fts uq_claim_statement; do
  FOUND="$(psql "${LEGACY_DRILL_SCRATCH_URL}" -Atc \
    "SELECT count(*) FROM pg_indexes WHERE indexname = '${index}'")"
  if [ "${FOUND}" != "1" ]; then
    echo "event=full_restore_drill outcome=fail reason=missing_index index=${index}" >&2
    exit 1
  fi
done
echo "drill3: schema ${SCRATCH_SCHEMA} and indexes present on scratch"

echo "drill3: step 4 post-restore verification (runbook 5)"
python3 - "${BACKUP_DIR}" "${LEGACY_DRILL_SCRATCH_URL}" "${SCRATCH_STORAGE}" <<'PY'
import hashlib, json, subprocess, sys
backup_dir, scratch_url, storage_dir = sys.argv[1], sys.argv[2], sys.argv[3]
manifest = json.load(open(f"{backup_dir}/manifest.json"))

def q(sql):
    return subprocess.run(
        ["psql", scratch_url, "-Atc", sql], capture_output=True, text=True, check=True
    ).stdout.strip()

# Row counts against the manifest, every table.
mismatches = []
for table, expected in sorted(manifest["row_counts"].items()):
    actual = int(q(f'SELECT count(*) FROM "{table}"'))
    if actual != expected:
        mismatches.append((table, expected, actual))
if mismatches:
    print(f"row count mismatches: {mismatches}", file=sys.stderr)
    sys.exit(1)
print(f"drill3: {len(manifest['row_counts'])} table row counts match the manifest")

# Audit-log continuity: the restored log reaches the manifest's last
# sequence number with the same entry count (append-only, ADR-11).
last_seq = int(q("SELECT COALESCE(MAX(sequence_number), 0) FROM audit_log_entry"))
if last_seq != manifest["audit_last_sequence"]:
    print(
        f"audit continuity broken: last sequence {last_seq} != "
        f"manifest {manifest['audit_last_sequence']}", file=sys.stderr,
    )
    sys.exit(1)
print(f"drill3: audit log continuous through sequence {last_seq}")

# Sampled content reads: artifact originals decrypt from the restored
# storage tree and match their recorded checksums.
rows = q(
    "SELECT id || '|' || checksum || '|' || storage_ref FROM artifact "
    "WHERE deleted_at IS NULL ORDER BY id LIMIT 3"
).splitlines()
if not rows:
    print("no artifacts to sample", file=sys.stderr)
    sys.exit(1)
for row in rows:
    artifact_id, checksum, ref = row.split("|")
    digest = hashlib.sha256(open(f"{storage_dir}/{ref}", "rb").read()).hexdigest()
    if digest != checksum:
        print(f"sampled read failed for artifact {artifact_id}", file=sys.stderr)
        sys.exit(1)
print(f"drill3: {len(rows)} sampled artifact reads verified byte-identical")
PY

echo "drill3: step 5 boot the API on the restored state and smoke-test"
# exec makes $! the server's real pid; output goes to a file so the server
# never holds this script's stdout open.
(
  cd "${REPO}/services/api" && exec env \
    LEGACY_ENV=local LEGACY_DATABASE_URL="${LEGACY_DRILL_SCRATCH_URL}" \
    LEGACY_STORAGE_DIR="${SCRATCH_STORAGE}" \
    .venv/bin/uvicorn legacy_api.main:app --host 127.0.0.1 --port "${PORT}" \
    --log-level warning
) > "${WORK}/api.log" 2>&1 &
API_PID=$!
for _ in $(seq 1 40); do
  if curl -fsS --max-time 2 "http://127.0.0.1:${PORT}/healthz" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done
"${REPO}/scripts/smoke_test.sh" "http://127.0.0.1:${PORT}" local
kill "${API_PID}" 2>/dev/null || true
API_PID=""

DURATION=$(( $(date +%s) - STARTED ))
if [ "${DURATION}" -gt "${RTO_TARGET}" ]; then
  echo "event=full_restore_drill outcome=fail reason=rto_exceeded duration_s=${DURATION} target_s=${RTO_TARGET}" >&2
  exit 1
fi
echo "event=full_restore_drill outcome=pass duration_s=${DURATION} rto_target_s=${RTO_TARGET} backup_dir=${BACKUP_DIR}"