#!/usr/bin/env bash
# RailYatra Minimum Production Smoke Test Suite for Linux / CI
# Exit Code 0 = PASS, 1 = FAIL

set -euo pipefail

BASE_URL="${1:-http://localhost:5000}"
AI_URL="${2:-http://localhost:8000}"
FAIL_COUNT=0

echo "====================================================================="
echo "STARTING RAILYATRA PRODUCTION SMOKE TEST SUITE (BASH)"
echo "Target Backend: $BASE_URL"
echo "Target AI Service: $AI_URL"
echo "====================================================================="

assert_test() {
  local test_name="$1"
  local condition="$2"
  local details="${3:-}"
  if [ "$condition" = "true" ]; then
    echo " [PASS] $test_name"
  else
    echo " [FAIL] $test_name - $details"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

# 1. Health Endpoints Check (Liveness/Readiness)
echo "Checking health endpoints..."

STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/health") || true
assert_test "Backend Liveness Check" "$( [ "$STATUS_CODE" -eq 200 ] && echo "true" || echo "false" )" "Status code: $STATUS_CODE"

STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/health/ready") || true
assert_test "Backend Readiness Check" "$( [ "$STATUS_CODE" -eq 200 ] && echo "true" || echo "false" )" "Status code: $STATUS_CODE"

STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$AI_URL/health") || true
assert_test "AI Service Liveness Check" "$( [ "$STATUS_CODE" -eq 200 ] && echo "true" || echo "false" )" "Status code: $STATUS_CODE"

# 2. User Registration
RANDOM_VAL=$((RANDOM % 9000 + 1000))
EMAIL="smoke_bash_$RANDOM_VAL@railyatra.com"
PASSWORD="SuperSecurePassword123!"
FULL_NAME="Smoke Bash User"

echo "Registering user: $EMAIL..."
REG_RESP=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\",\"fullName\":\"$FULL_NAME\"}" \
  "$BASE_URL/auth/register") || true

SUCCESS=$(echo "$REG_RESP" | grep -o '"success":true' || echo "false")
assert_test "User Registration Endpoint" "$( [ "$SUCCESS" = '"success":true' ] && echo "true" || echo "false" )" "Registration response failed: $REG_RESP"

# 3. User Login
echo "Logging in..."
LOGIN_RESP=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" \
  "$BASE_URL/auth/login") || true

SUCCESS=$(echo "$LOGIN_RESP" | grep -o '"success":true' || echo "false")
ACCESS_TOKEN=$(echo "$LOGIN_RESP" | grep -o '"accessToken":"[^"]*' | grep -o '[^"]*$' || echo "")

assert_test "User Login Endpoint" "$( [ "$SUCCESS" = '"success":true' ] && [ -n "$ACCESS_TOKEN" ] && echo "true" || echo "false" )" "Login failed or token empty"

if [ -n "$ACCESS_TOKEN" ]; then
  # 4. Auth-Protected Me Route
  ME_RESP=$(curl -s -X GET \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    "$BASE_URL/auth/me") || true
  
  SUCCESS=$(echo "$ME_RESP" | grep -o '"success":true' || echo "false")
  assert_test "Profile Recovery Check (Me Endpoint)" "$( [ "$SUCCESS" = '"success":true' ] && echo "true" || echo "false" )" "Profile recovery failed: $ME_RESP"

  # 5. Create Conversation
  CONV_RESP=$(curl -s -X POST \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"summary\":\"Smoke Test Conversation\"}" \
    "$BASE_URL/api/conversations") || true
  
  CONV_ID=$(echo "$CONV_RESP" | grep -o '"id":"[^"]*' | grep -o '[^"]*$' || echo "")
  assert_test "Create Conversation Endpoint" "$( [ -n "$CONV_ID" ] && echo "true" || echo "false" )" "Failed to create conversation: $CONV_RESP"

  if [ -n "$CONV_ID" ]; then
    # 6. Stream Chat Response
    CHAT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"message\":\"I want to search a train from NDLS to BGP\"}" \
      "$BASE_URL/api/conversations/$CONV_ID/chat") || true
    
    assert_test "AI Chat Stream Proxy Endpoint" "$( [ "$CHAT_STATUS" -eq 200 ] && echo "true" || echo "false" )" "Chat stream status: $CHAT_STATUS"

    # 7. Delete Conversation
    DELETE_RESP=$(curl -s -X DELETE \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      "$BASE_URL/api/conversations/$CONV_ID") || true
    
    SUCCESS=$(echo "$DELETE_RESP" | grep -o '"success":true' || echo "false")
    assert_test "Delete Conversation Endpoint" "$( [ "$SUCCESS" = '"success":true' ] && echo "true" || echo "false" )" "Failed to delete conversation: $DELETE_RESP"
  fi

  # 8. Notifications Fetch Check
  NOTIF_RESP=$(curl -s -X GET \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    "$BASE_URL/api/engagement/notifications") || true
  
  assert_test "Notifications Retrieval Endpoint" "$( [ -n "$NOTIF_RESP" ] && echo "true" || echo "false" )" "Empty notifications list"
fi

# 9. JWT Refresh Failure Rejection
REFRESH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/auth/refresh") || true
assert_test "JWT Refresh Failure Rejection" "$( [ "$REFRESH_STATUS" -eq 401 ] || [ "$REFRESH_STATUS" -eq 400 ] && echo "true" || echo "false" )" "Status code: $REFRESH_STATUS"

# 10. Invalid JWT Rejection
BAD_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET \
  -H "Authorization: Bearer invalid_token_here" \
  "$BASE_URL/auth/me") || true
assert_test "Invalid JWT Rejection" "$( [ "$BAD_STATUS" -eq 401 ] && echo "true" || echo "false" )" "Status code: $BAD_STATUS"

# 11. Unauthorized Endpoints Rejection
ANON_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET "$BASE_URL/auth/me") || true
assert_test "Unauthorized Endpoint Rejection" "$( [ "$ANON_STATUS" -eq 401 ] && echo "true" || echo "false" )" "Status code: $ANON_STATUS"

# 12. Journey Intelligence core engine test
INTEL_RESP=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d "{\"source\":\"NDLS\",\"destination\":\"BGP\",\"journey_date\":\"2026-07-28\",\"preferred_class\":\"3A\"}" \
  "$AI_URL/api/intelligence/analyze") || true

HAS_RECOMMENDATION=$(echo "$INTEL_RESP" | grep -E '("recommendations"|"options")' >/dev/null && echo "true" || echo "false")
assert_test "FastAPI Journey Intelligence Endpoint" "$HAS_RECOMMENDATION" "Response: $INTEL_RESP"

# 13. Logout Endpoint Check
LOGOUT_RESP=$(curl -s -X POST "$BASE_URL/auth/logout") || true
SUCCESS=$(echo "$LOGOUT_RESP" | grep -o '"success":true' || echo "false")
assert_test "User Logout Endpoint" "$( [ "$SUCCESS" = '"success":true' ] && echo "true" || echo "false" )" "Logout failed: $LOGOUT_RESP"

echo "====================================================================="
if [ "$FAIL_COUNT" -eq 0 ]; then
  echo "SUCCESS: ALL BASH SMOKE TESTS PASSED"
  exit 0
else
  echo "FAILURE: $FAIL_COUNT BASH SMOKE TESTS FAILED"
  exit 1
fi
