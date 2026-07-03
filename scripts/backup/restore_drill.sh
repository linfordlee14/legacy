#!/usr/bin/env bash
# Automated restore drill (BACKUP_AND_RECOVERY 4.7, runbook 2 automation;
# MVP-009 acceptance). Backs up the source, restores into a scratch
# database, and verifies: decryption, plaintext checksum, schema version,
# and per-table row counts against the manifest. A failed drill is SEV-1
# material (OBSERVABILITY 4.5).
#
# Env:
#   LEGACY_DRILL_SOURCE_URL   database to back up (synthetic or real)
#   LEGACY_DRILL_SCRATCH_URL  EMPTY scratch database to restore into
#   LEGACY_BACKUP_PUBLIC_KEY_FILE / LEGACY_BACKUP_PRIVATE_KEY_FILE
#       Key pair; with LEGACY_DRILL_GENERATE_KEYS=1 an ephemeral pair is
#       created (synthetic-data drills only; real drills use escrow keys).
set -euo pipefail

: "${LEGACY_DRILL_SOURCE_URL:?set LEGACY_DRILL_SOURCE_URL}"
: "${LEGACY_DRILL_SCRATCH_URL:?set LEGACY_DRILL_SCRATCH_URL}"
HERE="$(cd "$(dirname "$0")" && pwd)"
STARTED="$(date +%s)"
WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

if [ "${LEGACY_DRILL_GENERATE_KEYS:-0}" = "1" ]; then
  echo "drill: generating ephemeral key pair (synthetic data only)"
  openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 \
    -out "${WORK}/drill.key" 2>/dev/null
  openssl pkey -in "${WORK}/drill.key" -pubout -out "${WORK}/drill.pub"
  export LEGACY_BACKUP_PRIVATE_KEY_FILE="${WORK}/drill.key"
  export LEGACY_BACKUP_PUBLIC_KEY_FILE="${WORK}/drill.pub"
fi
: "${LEGACY_BACKUP_PUBLIC_KEY_FILE:?set LEGACY_BACKUP_PUBLIC_KEY_FILE}"
: "${LEGACY_BACKUP_PRIVATE_KEY_FILE:?set LEGACY_BACKUP_PRIVATE_KEY_FILE}"

echo "drill: backing up source"
LEGACY_BACKUP_DATABASE_URL="${LEGACY_DRILL_SOURCE_URL}" \
LEGACY_BACKUP_DIR="${WORK}/backups" \
  "${HERE}/backup.sh"
BACKUP_DIR="$(ls -d "${WORK}"/backups/*/ | head -1)"
BACKUP_DIR="${BACKUP_DIR%/}"

echo "drill: restoring to scratch"
"${HERE}/restore.sh" "${BACKUP_DIR}" "${LEGACY_DRILL_SCRATCH_URL}"

echo "drill: verifying row counts and schema version"
python3 - "$BACKUP_DIR" "$LEGACY_DRILL_SCRATCH_URL" <<'PY'
import json
import subprocess
import sys

backup_dir, scratch_url = sys.argv[1], sys.argv[2]
manifest = json.load(open(f"{backup_dir}/manifest.json"))

def psql(query: str) -> str:
    return subprocess.run(
        ["psql", scratch_url, "-Atc", query], check=True, capture_output=True, text=True
    ).stdout.strip()

schema = psql("SELECT version_num FROM alembic_version")
assert schema == manifest["schema_version"], (
    f"schema version mismatch: {schema} != {manifest['schema_version']}"
)

failures = []
for table, expected in sorted(manifest["row_counts"].items()):
    actual = int(psql(f'SELECT count(*) FROM "{table}"'))
    if actual != expected:
        failures.append(f"{table}: {actual} != {expected}")
assert not failures, "row count mismatches: " + "; ".join(failures)
print(f"drill verification: {len(manifest['row_counts'])} tables match, schema {schema}")
PY

DURATION=$(( $(date +%s) - STARTED ))
echo "event=restore_drill outcome=pass duration_s=${DURATION} backup_dir=${BACKUP_DIR}"
