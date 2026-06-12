#!/usr/bin/env bash
# Smoke test: register token → login → send (dry-run) → check history
# Requires: backend running at http://localhost:8000 with FCM_FAKE=1
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@example.com}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-changeme123}"

echo "=== PushNotify Smoke Test ==="
echo "Base URL: $BASE_URL"

# 1. Health check
echo ""
echo "1. Health check..."
HEALTH=$(curl -fsS "$BASE_URL/health")
echo "   Response: $HEALTH"
echo "$HEALTH" | grep -q '"ok"' || { echo "FAIL: health check"; exit 1; }
echo "   PASS"

# 2. Register a device token
echo ""
echo "2. Register device token..."
REGISTER=$(curl -fsS -X POST "$BASE_URL/api/v1/devices/register" \
  -H "Content-Type: application/json" \
  -d '{"fcm_token":"smoke-test-token-12345","platform":"android","app_version":"1.0"}')
echo "   Response: $REGISTER"
echo "$REGISTER" | grep -q '"registered":true' || { echo "FAIL: device registration"; exit 1; }
echo "   PASS"

# 3. Admin login
echo ""
echo "3. Admin login..."
LOGIN=$(curl -fsS -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASSWORD\"}")
echo "   Response: ${LOGIN:0:80}..."
TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
[ -n "$TOKEN" ] || { echo "FAIL: login (no token)"; exit 1; }
echo "   PASS (token obtained)"

# 4. Send notification (dry-run)
echo ""
echo "4. Send notification (dry-run)..."
SEND=$(curl -fsS -X POST "$BASE_URL/api/v1/messages/send" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"target":{"type":"broadcast"},"notification":{"title":"Smoke Test","body":"Hello from smoke test"},"dry_run":true}')
echo "   Response: $SEND"
echo "$SEND" | grep -q '"dry_run":true' || { echo "FAIL: send (dry_run not reflected)"; exit 1; }
echo "   PASS"

# 5. Check history
echo ""
echo "5. Check send history..."
HISTORY=$(curl -fsS "$BASE_URL/api/v1/messages/history" \
  -H "Authorization: Bearer $TOKEN")
echo "   Response: ${HISTORY:0:120}..."
echo "$HISTORY" | grep -q '"total"' || { echo "FAIL: history endpoint"; exit 1; }
echo "   PASS"

echo ""
echo "=== ALL SMOKE TESTS PASSED ==="
