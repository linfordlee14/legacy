#!/usr/bin/env bash
# Restore an encrypted backup into a target database
# (BACKUP_AND_RECOVERY 4.6, used by runbooks 1 to 3).
#
# Usage: restore.sh <backup_dir> <target_database_url>
# Env:   LEGACY_BACKUP_PRIVATE_KEY_FILE  owner-held RSA private key (PEM)
#
# The target must be a scratch or freshly created database; this script
# never points at production (runbook discipline, CI-09 for drills).
set -euo pipefail

BACKUP_DIR="${1:?usage: restore.sh <backup_dir> <target_database_url>}"
TARGET_URL="${2:?usage: restore.sh <backup_dir> <target_database_url>}"
: "${LEGACY_BACKUP_PRIVATE_KEY_FILE:?set LEGACY_BACKUP_PRIVATE_KEY_FILE}"

WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

echo "restore: decrypting data key"
openssl pkeyutl -decrypt -inkey "${LEGACY_BACKUP_PRIVATE_KEY_FILE}" \
  -pkeyopt rsa_padding_mode:oaep -pkeyopt rsa_oaep_md:sha256 \
  -in "${BACKUP_DIR}/data.key.enc" -out "${WORK}/data.key"

echo "restore: decrypting dump"
openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 \
  -in "${BACKUP_DIR}/dump.enc" -out "${WORK}/dump.pgcustom" -pass "file:${WORK}/data.key"

EXPECTED_SHA="$(python3 -c "import json;print(json.load(open('${BACKUP_DIR}/manifest.json'))['plaintext_sha256'])")"
ACTUAL_SHA="$(sha256sum "${WORK}/dump.pgcustom" | cut -d' ' -f1)"
if [ "${EXPECTED_SHA}" != "${ACTUAL_SHA}" ]; then
  echo "event=restore outcome=fail reason=checksum_mismatch" >&2
  exit 1
fi
echo "restore: checksum verified"

pg_restore --no-owner --dbname="${TARGET_URL}" "${WORK}/dump.pgcustom"
echo "event=restore outcome=ok backup_dir=${BACKUP_DIR}"
