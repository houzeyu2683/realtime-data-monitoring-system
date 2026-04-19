#!/usr/bin/env bash
# 驗收測試腳本 — 自動執行所有可 curl 驗證的 TC，最後清除測試資料
# 使用方式：bash scripts/run_acceptance_tests.sh [BASE_URL]
# 預設 BASE_URL=http://localhost:8000

set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
PASS=0
FAIL=0
CREATED_RECORD_IDS=()
CREATED_USER_IDS=()

GREEN="\033[0;32m"
RED="\033[0;31m"
RESET="\033[0m"

check() {
    local tc="$1" desc="$2" expected="$3" actual="$4"
    if [ "$actual" = "$expected" ]; then
        echo -e "${GREEN}✅ $tc${RESET} $desc → $actual"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}❌ $tc${RESET} $desc → expected=$expected actual=$actual"
        FAIL=$((FAIL + 1))
    fi
}

# ─── 準備 Token ────────────────────────────────────────────────────────────────

echo "=== 準備 Token ==="

ADMIN_TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin1234"}' | jq -r '.access_token')

# 建立測試用帳號（若已存在則忽略）
curl -s -X POST "$BASE_URL/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d '{"username":"at_normaluser","email":"at_normal@test.com","password":"password123"}' > /dev/null 2>&1 || true

curl -s -X POST "$BASE_URL/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d '{"username":"at_vieweruser","email":"at_viewer@test.com","password":"password123"}' > /dev/null 2>&1 || true

USER_TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"at_normaluser","password":"password123"}' | jq -r '.access_token')

USER_ID=$(curl -s "$BASE_URL/api/v1/auth/me" \
    -H "Authorization: Bearer $USER_TOKEN" | jq -r '.id')
CREATED_USER_IDS+=("$USER_ID")

VIEWER_ID=$(curl -s "$BASE_URL/api/v1/auth/me" \
    -H "Authorization: Bearer $(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username":"at_vieweruser","password":"password123"}' | jq -r '.access_token')" | jq -r '.id')
CREATED_USER_IDS+=("$VIEWER_ID")

curl -s -X PATCH "$BASE_URL/api/v1/users/$VIEWER_ID" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"role":"viewer"}' > /dev/null

VIEWER_TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"at_vieweruser","password":"password123"}' | jq -r '.access_token')

ADMIN_ID=$(curl -s "$BASE_URL/api/v1/auth/me" \
    -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.id')

echo "Token 準備完成 (USER_ID=$USER_ID, VIEWER_ID=$VIEWER_ID)"
echo ""

# ─── Module 1: Auth ────────────────────────────────────────────────────────────

echo "=== Module 1: Auth ==="

check "TC-AUTH-001" "正確帳密登入 → 200" "200" \
    "$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username":"admin","password":"admin1234"}')"

check "TC-AUTH-002" "錯誤密碼登入 → 401" "401" \
    "$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username":"admin","password":"wrongpass"}')"

check "TC-AUTH-003" "不存在帳號登入 → 401" "401" \
    "$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username":"ghost","password":"password123"}')"

# TC-AUTH-004: 建立停用帳號測試
AT4_RESP=$(curl -s -X POST "$BASE_URL/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d '{"username":"at_inactive","email":"at_inactive@test.com","password":"password123"}')
AT4_ID=$(echo "$AT4_RESP" | jq -r '.id // empty')
if [ -n "$AT4_ID" ]; then
    CREATED_USER_IDS+=("$AT4_ID")
    curl -s -X PATCH "$BASE_URL/api/v1/users/$AT4_ID" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"is_active":false}' > /dev/null
fi
check "TC-AUTH-004" "停用帳號登入 → 403" "403" \
    "$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username":"at_inactive","password":"password123"}')"

AT5_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d '{"username":"at_newuser","email":"at_newuser@test.com","password":"password123"}')
AT5_CODE=$(echo "$AT5_RESP" | tail -1)
AT5_ID=$(echo "$AT5_RESP" | head -1 | jq -r '.id // empty')
[ -n "$AT5_ID" ] && CREATED_USER_IDS+=("$AT5_ID")
check "TC-AUTH-005" "正常註冊 → 201" "201" "$AT5_CODE"

check "TC-AUTH-006" "重複 username 註冊 → 409" "409" \
    "$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/auth/register" \
        -H "Content-Type: application/json" \
        -d '{"username":"admin","email":"dup@test.com","password":"password123"}')"

check "TC-AUTH-007" "重複 email 註冊 → 409" "409" \
    "$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/auth/register" \
        -H "Content-Type: application/json" \
        -d '{"username":"at_other","email":"at_normal@test.com","password":"password123"}')"

check "TC-AUTH-008" "取得自身資料 → 200" "200" \
    "$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/auth/me" \
        -H "Authorization: Bearer $ADMIN_TOKEN")"

check "TC-AUTH-009" "無效 token 存取 → 401" "401" \
    "$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/auth/me" \
        -H "Authorization: Bearer invalid.token.here")"

echo ""

# ─── Module 2: User Management ────────────────────────────────────────────────

echo "=== Module 2: User Management ==="

check "TC-USER-001" "Admin 取得使用者列表 → 200" "200" \
    "$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/users/" \
        -H "Authorization: Bearer $ADMIN_TOKEN")"

check "TC-USER-002" "非 Admin 取得使用者列表 → 403" "403" \
    "$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/users/" \
        -H "Authorization: Bearer $USER_TOKEN")"

check "TC-USER-003" "取得自身使用者資料 → 200" "200" \
    "$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/users/$USER_ID" \
        -H "Authorization: Bearer $USER_TOKEN")"

check "TC-USER-004" "非 Admin 取得他人資料 → 403" "403" \
    "$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/users/$ADMIN_ID" \
        -H "Authorization: Bearer $USER_TOKEN")"

check "TC-USER-005" "Admin 修改他人角色 → 200" "200" \
    "$(curl -s -o /dev/null -w "%{http_code}" -X PATCH "$BASE_URL/api/v1/users/$USER_ID" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"role":"viewer"}')"

check "TC-USER-006" "User 嘗試修改角色 → 403" "403" \
    "$(curl -s -o /dev/null -w "%{http_code}" -X PATCH "$BASE_URL/api/v1/users/$USER_ID" \
        -H "Authorization: Bearer $USER_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"role":"admin"}')"

check "TC-USER-007" "Admin 停用帳號 → 200" "200" \
    "$(curl -s -o /dev/null -w "%{http_code}" -X PATCH "$BASE_URL/api/v1/users/$USER_ID" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"is_active":false}')"

# 恢復 normaluser 以便後續 Data TC
curl -s -X PATCH "$BASE_URL/api/v1/users/$USER_ID" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"is_active":true,"role":"user"}' > /dev/null
USER_TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"at_normaluser","password":"password123"}' | jq -r '.access_token')

echo ""

# ─── Module 3: Data Management ────────────────────────────────────────────────

echo "=== Module 3: Data Management ==="

RECORD_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/data/" \
    -H "Authorization: Bearer $USER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"title":"Sensor A","value":50.0,"category":"temperature","threshold":80.0}')
RECORD_CODE=$(echo "$RECORD_RESP" | tail -1)
RECORD_ID=$(echo "$RECORD_RESP" | head -1 | jq -r '.id // empty')
[ -n "$RECORD_ID" ] && CREATED_RECORD_IDS+=("$RECORD_ID")
check "TC-DATA-001" "User 新增資料記錄 → 201" "201" "$RECORD_CODE"

check "TC-DATA-002" "Viewer 嘗試新增資料 → 403" "403" \
    "$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/data/" \
        -H "Authorization: Bearer $VIEWER_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"title":"Sensor A","value":50.0,"category":"temperature"}')"

for i in 1 2 3 4 5; do
    RID=$(curl -s -X POST "$BASE_URL/api/v1/data/" \
        -H "Authorization: Bearer $USER_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"title\":\"Record $i\",\"value\":$((i*10)).0,\"category\":\"temperature\"}" | jq -r '.id // empty')
    [ -n "$RID" ] && CREATED_RECORD_IDS+=("$RID")
done
ITEMS_COUNT=$(curl -s "$BASE_URL/api/v1/data/?page=1&size=3" \
    -H "Authorization: Bearer $USER_TOKEN" | jq '.items | length')
check "TC-DATA-003" "取得資料列表（分頁）items_count=3 → 3" "3" "$ITEMS_COUNT"

HUM_RID=$(curl -s -X POST "$BASE_URL/api/v1/data/" \
    -H "Authorization: Bearer $USER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"title":"Humid","value":60.0,"category":"humidity"}' | jq -r '.id // empty')
[ -n "$HUM_RID" ] && CREATED_RECORD_IDS+=("$HUM_RID")
CAT_UNIQUE=$(curl -s "$BASE_URL/api/v1/data/?category=humidity" \
    -H "Authorization: Bearer $USER_TOKEN" | jq '[.items[].category] | unique | length')
check "TC-DATA-004" "依分類篩選，唯一分類數=1 → 1" "1" "$CAT_UNIQUE"

check "TC-DATA-005" "依時間範圍篩選 → 200" "200" \
    "$(curl -s -o /dev/null -w "%{http_code}" \
        "$BASE_URL/api/v1/data/?start_time=2020-01-01T00:00:00&end_time=2099-12-31T00:00:00" \
        -H "Authorization: Bearer $USER_TOKEN")"

SORTED=$(curl -s "$BASE_URL/api/v1/data/?sort_by=value&sort_order=asc&size=5" \
    -H "Authorization: Bearer $USER_TOKEN" | jq '[.items[].value] | . == (sort)')
check "TC-DATA-006" "排序功能（asc）→ true" "true" "$SORTED"

check "TC-DATA-007" "創建者更新自己的資料 → 200" "200" \
    "$(curl -s -o /dev/null -w "%{http_code}" -X PATCH "$BASE_URL/api/v1/data/$RECORD_ID" \
        -H "Authorization: Bearer $USER_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"title":"Updated Title"}')"

ADMIN_REC_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/data/" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"title":"Admin Record","value":50.0,"category":"temperature"}')
ADMIN_REC_ID=$(echo "$ADMIN_REC_RESP" | head -1 | jq -r '.id // empty')
[ -n "$ADMIN_REC_ID" ] && CREATED_RECORD_IDS+=("$ADMIN_REC_ID")

check "TC-DATA-008" "非創建者更新資料 → 403" "403" \
    "$(curl -s -o /dev/null -w "%{http_code}" -X PATCH "$BASE_URL/api/v1/data/$ADMIN_REC_ID" \
        -H "Authorization: Bearer $USER_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"title":"Hacked"}')"

check "TC-DATA-009" "Admin 更新任意資料 → 200" "200" \
    "$(curl -s -o /dev/null -w "%{http_code}" -X PATCH "$BASE_URL/api/v1/data/$RECORD_ID" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"title":"Admin Updated"}')"

DEL_RID=$(curl -s -X POST "$BASE_URL/api/v1/data/" \
    -H "Authorization: Bearer $USER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"title":"To Delete","value":10.0,"category":"temperature"}' | jq -r '.id // empty')
check "TC-DATA-010" "創建者刪除自己的資料 → 204" "204" \
    "$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "$BASE_URL/api/v1/data/$DEL_RID" \
        -H "Authorization: Bearer $USER_TOKEN")"

check "TC-DATA-011" "非創建者刪除資料 → 403" "403" \
    "$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "$BASE_URL/api/v1/data/$ADMIN_REC_ID" \
        -H "Authorization: Bearer $USER_TOKEN")"

check "TC-DATA-012" "刪除不存在的資料 → 404" "404" \
    "$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "$BASE_URL/api/v1/data/99999" \
        -H "Authorization: Bearer $USER_TOKEN")"

ANOMALY=$(curl -s -X POST "$BASE_URL/api/v1/data/" \
    -H "Authorization: Bearer $USER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"title":"Hot Sensor","value":90.0,"category":"temperature","threshold":80.0}')
ANOMALY_ID=$(echo "$ANOMALY" | jq -r '.id // empty')
[ -n "$ANOMALY_ID" ] && CREATED_RECORD_IDS+=("$ANOMALY_ID")
check "TC-DATA-013" "數值超過閾值標記異常 → true" "true" \
    "$(echo "$ANOMALY" | jq -r '.is_anomaly')"

check "TC-DATA-014" "CSV 批量導入 → 201" "201" \
    "$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/v1/data/import/csv" \
        -H "Authorization: Bearer $USER_TOKEN" \
        -F "file=@sample_data.csv")"

echo '[{"title":"J1","value":55.0,"category":"cpu_load"},{"title":"J2","value":70.0,"category":"memory_usage"}]' > /tmp/at_test.json
JSON_IMPORTED=$(curl -s -X POST "$BASE_URL/api/v1/data/import/json" \
    -H "Authorization: Bearer $USER_TOKEN" \
    -F "file=@/tmp/at_test.json" | jq -r '.imported')
check "TC-DATA-015" "JSON 批量導入 imported=2 → 2" "2" "$JSON_IMPORTED"
rm -f /tmp/at_test.json

echo ""

# ─── Module 4: Analytics ──────────────────────────────────────────────────────

echo "=== Module 4: Analytics ==="

check "TC-ANA-001" "取得統計摘要 → 200" "200" \
    "$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/analytics/" \
        -H "Authorization: Bearer $USER_TOKEN")"

ANA_TOTAL=$(curl -s "$BASE_URL/api/v1/analytics/?start_time=2020-01-01T00:00:00&end_time=2099-12-31T00:00:00" \
    -H "Authorization: Bearer $USER_TOKEN" | jq '.summary.total')
check "TC-ANA-002" "依時間範圍統計 total >= 1" "true" \
    "$([ "$ANA_TOTAL" -ge 1 ] && echo true || echo false)"

check "TC-ANA-003" "依分類統計 → 200" "200" \
    "$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/analytics/?category=humidity" \
        -H "Authorization: Bearer $USER_TOKEN")"

check "TC-ANA-004" "分類聚合資料 → 200" "200" \
    "$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/analytics/" \
        -H "Authorization: Bearer $USER_TOKEN")"

check "TC-ANA-005" "趨勢資料（小時）→ array" "array" \
    "$(curl -s "$BASE_URL/api/v1/analytics/?trend_interval=hour" \
        -H "Authorization: Bearer $USER_TOKEN" | jq -r '.trend | type')"

check "TC-ANA-006" "趨勢資料（天）→ array" "array" \
    "$(curl -s "$BASE_URL/api/v1/analytics/?trend_interval=day" \
        -H "Authorization: Bearer $USER_TOKEN" | jq -r '.trend | type')"

check "TC-ANA-007" "匯出 Excel → 200" "200" \
    "$(curl -s -o /tmp/at_export.xlsx -w "%{http_code}" \
        "$BASE_URL/api/v1/analytics/export/excel" \
        -H "Authorization: Bearer $USER_TOKEN")"
rm -f /tmp/at_export.xlsx

echo ""

# ─── Module 5: Admin ──────────────────────────────────────────────────────────

echo "=== Module 5: Admin ==="

check "TC-ADM-001" "Admin 取得系統日誌 → 200" "200" \
    "$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/admin/logs" \
        -H "Authorization: Bearer $ADMIN_TOKEN")"

check "TC-ADM-002" "非 Admin 取得系統日誌 → 403" "403" \
    "$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/admin/logs" \
        -H "Authorization: Bearer $USER_TOKEN")"

check "TC-ADM-003" "系統日誌分頁 → 200" "200" \
    "$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/admin/logs?page=1&size=50" \
        -H "Authorization: Bearer $ADMIN_TOKEN")"

check "TC-ADM-004" "取得資料庫狀態 → 200" "200" \
    "$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/admin/db-status" \
        -H "Authorization: Bearer $ADMIN_TOKEN")"

curl -s -X POST "$BASE_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin1234"}' > /dev/null
LOGIN_IN_LOG=$(curl -s "$BASE_URL/api/v1/admin/logs?size=100" \
    -H "Authorization: Bearer $ADMIN_TOKEN" | jq '[.items[].action] | contains(["login"])')
check "TC-ADM-005" "登入行為寫入日誌 → true" "true" "$LOGIN_IN_LOG"

AT6_REG_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d '{"username":"at_logtestuser","email":"at_logtest@test.com","password":"password123"}')
AT6_ID=$(echo "$AT6_REG_RESP" | head -1 | jq -r '.id // empty')
[ -n "$AT6_ID" ] && CREATED_USER_IDS+=("$AT6_ID")
REG_IN_LOG=$(curl -s "$BASE_URL/api/v1/admin/logs?size=100" \
    -H "Authorization: Bearer $ADMIN_TOKEN" | jq '[.items[].action] | contains(["register"])')
check "TC-ADM-006" "註冊行為寫入日誌 → true" "true" "$REG_IN_LOG"

echo ""

# ─── 清除測試資料 ──────────────────────────────────────────────────────────────

echo "=== 清除測試資料 ==="

for rid in "${CREATED_RECORD_IDS[@]}"; do
    curl -s -o /dev/null -X DELETE "$BASE_URL/api/v1/data/$rid" \
        -H "Authorization: Bearer $ADMIN_TOKEN" || true
done
echo "刪除 ${#CREATED_RECORD_IDS[@]} 筆資料記錄"

for uid in "${CREATED_USER_IDS[@]}"; do
    curl -s -o /dev/null -X DELETE "$BASE_URL/api/v1/users/$uid" \
        -H "Authorization: Bearer $ADMIN_TOKEN" || true
done
echo "刪除 ${#CREATED_USER_IDS[@]} 個測試帳號"

echo ""

# ─── 結果摘要 ─────────────────────────────────────────────────────────────────

echo "=============================="
echo -e "結果：${GREEN}✅ $PASS 通過${RESET}  ${RED}❌ $FAIL 失敗${RESET}"
echo "=============================="

[ "$FAIL" -eq 0 ] && exit 0 || exit 1
