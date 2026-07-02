#!/usr/bin/env bash
# Post-deploy smoke test (DEP-23 step 4, DEP-06 environment identity).
# Usage: scripts/smoke_test.sh [base_url] [expected_environment]
set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
EXPECTED_ENV="${2:-local}"

check() {
  local endpoint="$1"
  local body
  body="$(curl -fsS --max-time 10 "${BASE_URL}${endpoint}")"
  python3 - "$body" "$EXPECTED_ENV" "$endpoint" <<'PY'
import json, sys
body, expected_env, endpoint = sys.argv[1], sys.argv[2], sys.argv[3]
data = json.loads(body)
assert data["status"] == "ok", f"{endpoint}: status is {data['status']}"
assert data["environment"] == expected_env, (
    f"{endpoint}: environment is {data['environment']}, expected {expected_env}"
)
print(f"ok {endpoint} service={data['service']} version={data['version']} environment={data['environment']}")
PY
}

check /healthz
check /readyz
echo "smoke test passed: ${BASE_URL} is ${EXPECTED_ENV}"
