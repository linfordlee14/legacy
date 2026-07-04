#!/usr/bin/env bash
# Encrypted full database backup (BACKUP_AND_RECOVERY 4.2 to 4.4).
#
# Hybrid encryption honoring DEP-22: a random per-backup data key encrypts the
# dump (AES-256-CBC, PBKDF2); the data key is encrypted to the owner's RSA
# public key (RSA-OAEP). Only the public key exists in the backup
# environment; the private key is owner-held and escrowed. The manifest
# records checksums and per-table row counts for restore verification (the
# 0-errors element of 4.1).
#
# Env:
#   LEGACY_BACKUP_DATABASE_URL     source database (a dedicated read-only
#                                  backup role, never the app credential)
#   LEGACY_BACKUP_PUBLIC_KEY_FILE  owner's RSA public key (PEM)
#   LEGACY_BACKUP_DIR              output root (default ./backups)
set -euo pipefail

: "${LEGACY_BACKUP_DATABASE_URL:?set LEGACY_BACKUP_DATABASE_URL}"
: "${LEGACY_BACKUP_PUBLIC_KEY_FILE:?set LEGACY_BACKUP_PUBLIC_KEY_FILE}"
BACKUP_ROOT="${LEGACY_BACKUP_DIR:-./backups}"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="${BACKUP_ROOT}/${STAMP}"
mkdir -p "${OUT}"
WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

echo "backup: dumping database"
pg_dump --format=custom --no-owner --file="${WORK}/dump.pgcustom" "${LEGACY_BACKUP_DATABASE_URL}"

PLAINTEXT_SHA="$(sha256sum "${WORK}/dump.pgcustom" | cut -d' ' -f1)"
PLAINTEXT_BYTES="$(stat -c%s "${WORK}/dump.pgcustom")"

ROW_COUNTS="$(psql "${LEGACY_BACKUP_DATABASE_URL}" -Atc "
  SELECT coalesce(json_object_agg(t, c), '{}'::json) FROM (
    SELECT tablename AS t,
           (xpath('/row/cnt/text()',
                  query_to_xml(format('SELECT count(*) AS cnt FROM %I', tablename),
                               false, true, '')))[1]::text::bigint AS c
    FROM pg_tables WHERE schemaname = 'public'
  ) s;")"
SCHEMA_VERSION="$(psql "${LEGACY_BACKUP_DATABASE_URL}" -Atc \
  "SELECT version_num FROM alembic_version" 2>/dev/null || echo "none")"
AUDIT_LAST_SEQ="$(psql "${LEGACY_BACKUP_DATABASE_URL}" -Atc \
  "SELECT COALESCE(MAX(sequence_number), 0) FROM audit_log_entry" 2>/dev/null || echo 0)"

# Object storage tree (coverage table 4.2: originals are backed up).
# Optional so database-only invocations keep working, but its absence is
# loud, never silent.
STORAGE_SHA=""
STORAGE_BYTES=0
STORAGE_FILES=0
if [ -n "${LEGACY_BACKUP_STORAGE_DIR:-}" ] && [ -d "${LEGACY_BACKUP_STORAGE_DIR}" ]; then
  echo "backup: archiving object storage"
  tar -C "${LEGACY_BACKUP_STORAGE_DIR}" -cf "${WORK}/storage.tar" .
  STORAGE_SHA="$(sha256sum "${WORK}/storage.tar" | cut -d' ' -f1)"
  STORAGE_BYTES="$(stat -c%s "${WORK}/storage.tar")"
  STORAGE_FILES="$(find "${LEGACY_BACKUP_STORAGE_DIR}" -type f | wc -l | tr -d ' ')"
else
  echo "backup: WARNING object storage NOT included; set LEGACY_BACKUP_STORAGE_DIR (BACKUP_AND_RECOVERY 4.2)" >&2
fi

echo "backup: encrypting"
openssl rand -out "${WORK}/data.key" 64
openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt \
  -in "${WORK}/dump.pgcustom" -out "${OUT}/dump.enc" -pass "file:${WORK}/data.key"
if [ -n "${STORAGE_SHA}" ]; then
  openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt \
    -in "${WORK}/storage.tar" -out "${OUT}/storage.enc" -pass "file:${WORK}/data.key"
fi
openssl pkeyutl -encrypt -pubin -inkey "${LEGACY_BACKUP_PUBLIC_KEY_FILE}" \
  -pkeyopt rsa_padding_mode:oaep -pkeyopt rsa_oaep_md:sha256 \
  -in "${WORK}/data.key" -out "${OUT}/data.key.enc"

CIPHERTEXT_SHA="$(sha256sum "${OUT}/dump.enc" | cut -d' ' -f1)"
KEY_FINGERPRINT="$(openssl pkey -pubin -in "${LEGACY_BACKUP_PUBLIC_KEY_FILE}" \
  -outform DER 2>/dev/null | sha256sum | cut -c1-16)"

python3 - "$OUT" <<PY
import json, sys
storage_sha = "${STORAGE_SHA}"
manifest = {
    "created_at": "${STAMP}",
    "format": "pg_dump custom, aes-256-cbc pbkdf2, rsa-oaep data key",
    "plaintext_sha256": "${PLAINTEXT_SHA}",
    "plaintext_bytes": ${PLAINTEXT_BYTES},
    "ciphertext_sha256": "${CIPHERTEXT_SHA}",
    "public_key_fingerprint": "${KEY_FINGERPRINT}",
    "schema_version": "${SCHEMA_VERSION}",
    "audit_last_sequence": int("${AUDIT_LAST_SEQ}" or 0),
    "row_counts": json.loads('''${ROW_COUNTS}'''),
    "storage": (
        {"sha256": storage_sha, "bytes": ${STORAGE_BYTES},
         "file_count": ${STORAGE_FILES}}
        if storage_sha else None
    ),
}
with open(sys.argv[1] + "/manifest.json", "w") as f:
    json.dump(manifest, f, indent=2, sort_keys=True)
PY

echo "backup: complete at ${OUT}"
echo "event=backup outcome=ok backup_dir=${OUT} bytes=${PLAINTEXT_BYTES} schema=${SCHEMA_VERSION}"
