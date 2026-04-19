# 手動驗收測試操作手冊

**環境前置條件**
1. 執行 `docker compose up --build`
2. Swagger UI：`http://localhost:8000/docs`
3. 前端：`http://localhost:8501`
4. 自動化腳本需安裝 `jq`：`sudo apt install jq` / `brew install jq`

---

## 準備：取得 Token

**Swagger**：展開 `POST /api/v1/auth/login`，輸入帳密，複製 `access_token`，點右上角 Authorize 貼上。

**curl**：
```bash
export ADMIN_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin1234"}' | jq -r '.access_token')
```

---

## Module 1: Auth（使用者認證）

### TC-AUTH-001 正確帳密登入
**步驟**：`POST /api/v1/auth/login`，body：`{"username":"admin","password":"admin1234"}`
✅ 預期：200 + `access_token`
```bash
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin1234"}'
# 預期輸出：200
```

### TC-AUTH-002 錯誤密碼登入
**步驟**：`POST /api/v1/auth/login`，使用錯誤密碼
✅ 預期：401
```bash
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"wrongpass"}'
# 預期輸出：401
```

### TC-AUTH-003 不存在帳號登入
**步驟**：`POST /api/v1/auth/login`，使用不存在的 username
✅ 預期：401
```bash
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"ghost","password":"password123"}'
# 預期輸出：401
```

### TC-AUTH-004 停用帳號登入
**步驟**：先建立帳號並停用，再嘗試登入
✅ 預期：403
```bash
# 1. 建立帳號
INACTIVE_ID=$(curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"inactive_test","email":"inactive@test.com","password":"password123"}' | jq -r '.id')

# 2. Admin 停用帳號
curl -s -o /dev/null -X PATCH http://localhost:8000/api/v1/users/$INACTIVE_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_active":false}'

# 3. 嘗試登入
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"inactive_test","password":"password123"}'
# 預期輸出：403
```

### TC-AUTH-005 正常註冊
**步驟**：`POST /api/v1/auth/register`，合法資料
✅ 預期：201 + user 資料，`role` 為 `user`
```bash
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"newuser","email":"newuser@test.com","password":"password123"}'
# 預期輸出：201
```

### TC-AUTH-006 重複 username 註冊
**步驟**：`POST /api/v1/auth/register`，使用已存在的 username
✅ 預期：409
```bash
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","email":"other@test.com","password":"password123"}'
# 預期輸出：409
```

### TC-AUTH-007 重複 email 註冊
**步驟**：`POST /api/v1/auth/register`，使用已存在的 email
✅ 預期：409
```bash
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"other","email":"admin@example.com","password":"password123"}'
# 預期輸出：409
```

### TC-AUTH-008 取得自身資料
**步驟**：`GET /api/v1/auth/me`，帶有效 token
✅ 預期：200 + user 資料
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $ADMIN_TOKEN"
# 預期輸出：200
```

### TC-AUTH-009 無效 token 存取
**步驟**：`GET /api/v1/auth/me`，帶假 token
✅ 預期：401
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer invalid.token.here"
# 預期輸出：401
```

---

## Module 2: User Management（使用者管理）

```bash
# 建立一般 user 並取得 token
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"normaluser","email":"normal@test.com","password":"password123"}' > /dev/null

export USER_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"normaluser","password":"password123"}' | jq -r '.access_token')

export USER_ID=$(curl -s http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $USER_TOKEN" | jq -r '.id')
```

### TC-USER-001 Admin 取得使用者列表
**步驟**：Admin token，`GET /api/v1/users/`
✅ 預期：200 + 使用者陣列
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/users/ \
  -H "Authorization: Bearer $ADMIN_TOKEN"
# 預期輸出：200
```

### TC-USER-002 非 Admin 取得使用者列表
**步驟**：一般 user token，`GET /api/v1/users/`
✅ 預期：403
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/users/ \
  -H "Authorization: Bearer $USER_TOKEN"
# 預期輸出：403
```

### TC-USER-003 取得自身使用者資料
**步驟**：`GET /api/v1/users/{自己的id}`
✅ 預期：200
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/users/$USER_ID \
  -H "Authorization: Bearer $USER_TOKEN"
# 預期輸出：200
```

### TC-USER-004 取得他人資料（非 Admin）
**步驟**：一般 user token，`GET /api/v1/users/{admin_id}`
✅ 預期：403
```bash
ADMIN_ID=$(curl -s http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.id')

curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/users/$ADMIN_ID \
  -H "Authorization: Bearer $USER_TOKEN"
# 預期輸出：403
```

### TC-USER-005 Admin 修改他人角色
**步驟**：Admin token，`PATCH /api/v1/users/{id}`，`role: viewer`
✅ 預期：200，`role` 變為 `viewer`
```bash
curl -s -o /dev/null -w "%{http_code}" -X PATCH http://localhost:8000/api/v1/users/$USER_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role":"viewer"}'
# 預期輸出：200
```

### TC-USER-006 User 嘗試修改角色
**步驟**：一般 user token，`PATCH /api/v1/users/{id}`，`role: admin`
✅ 預期：403
```bash
curl -s -o /dev/null -w "%{http_code}" -X PATCH http://localhost:8000/api/v1/users/$USER_ID \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role":"admin"}'
# 預期輸出：403
```

### TC-USER-007 Admin 停用帳號
**步驟**：Admin token，`PATCH /api/v1/users/{id}`，`is_active: false`
✅ 預期：200，`is_active` 變為 `false`
```bash
curl -s -o /dev/null -w "%{http_code}" -X PATCH http://localhost:8000/api/v1/users/$USER_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_active":false}'
# 預期輸出：200
```

---

## Module 3: Data Management（資料管理）

```bash
# 重新啟用 normaluser 並取得 user token（若已停用）
curl -s -X PATCH http://localhost:8000/api/v1/users/$USER_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_active":true,"role":"user"}' > /dev/null

export USER_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"normaluser","password":"password123"}' | jq -r '.access_token')

# 建立 viewer token
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"vieweruser","email":"viewer@test.com","password":"password123"}' > /dev/null

VIEWER_ID=$(curl -s http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $(curl -s -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"vieweruser","password":"password123"}' | jq -r '.access_token')" | jq -r '.id')

curl -s -X PATCH http://localhost:8000/api/v1/users/$VIEWER_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role":"viewer"}' > /dev/null

export VIEWER_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"vieweruser","password":"password123"}' | jq -r '.access_token')
```

### TC-DATA-001 User 新增資料記錄
✅ 預期：201
```bash
export RECORD_ID=$(curl -s -X POST http://localhost:8000/api/v1/data/ \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Sensor A","value":50.0,"category":"temperature","threshold":80.0}' | jq -r '.id')
echo "Status should be 201, RECORD_ID=$RECORD_ID"
```

### TC-DATA-002 Viewer 嘗試新增資料
✅ 預期：403
```bash
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/data/ \
  -H "Authorization: Bearer $VIEWER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Sensor A","value":50.0,"category":"temperature"}'
# 預期輸出：403
```

### TC-DATA-003 取得資料列表（分頁）
✅ 預期：200，`items` 長度 ≤ size，`total` 正確
```bash
# 先新增數筆資料
for i in 1 2 3 4 5; do
  curl -s -X POST http://localhost:8000/api/v1/data/ \
    -H "Authorization: Bearer $USER_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"title\":\"Record $i\",\"value\":$((i*10)).0,\"category\":\"temperature\"}" > /dev/null
done

curl -s "http://localhost:8000/api/v1/data/?page=1&size=3" \
  -H "Authorization: Bearer $USER_TOKEN" | jq '{total, items_count: (.items | length)}'
# 預期：items_count=3
```

### TC-DATA-004 依分類篩選資料
✅ 預期：所有 items 的 category 皆為 `humidity`
```bash
curl -s -X POST http://localhost:8000/api/v1/data/ \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Humid","value":60.0,"category":"humidity"}' > /dev/null

curl -s "http://localhost:8000/api/v1/data/?category=humidity" \
  -H "Authorization: Bearer $USER_TOKEN" | jq '[.items[].category] | unique'
# 預期輸出：["humidity"]
```

### TC-DATA-005 依時間範圍篩選
✅ 預期：200
```bash
curl -s -o /dev/null -w "%{http_code}" \
  "http://localhost:8000/api/v1/data/?start_time=2020-01-01T00:00:00&end_time=2099-12-31T00:00:00" \
  -H "Authorization: Bearer $USER_TOKEN"
# 預期輸出：200
```

### TC-DATA-006 排序功能
✅ 預期：value 由小到大
```bash
curl -s "http://localhost:8000/api/v1/data/?sort_by=value&sort_order=asc" \
  -H "Authorization: Bearer $USER_TOKEN" | jq '[.items[].value]'
# 預期輸出：遞增數列
```

### TC-DATA-007 創建者更新自己的資料
✅ 預期：200
```bash
curl -s -o /dev/null -w "%{http_code}" -X PATCH http://localhost:8000/api/v1/data/$RECORD_ID \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Updated Title"}'
# 預期輸出：200
```

### TC-DATA-008 非創建者更新資料
✅ 預期：403
```bash
ADMIN_RECORD_ID=$(curl -s -X POST http://localhost:8000/api/v1/data/ \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Admin Record","value":50.0,"category":"temperature"}' | jq -r '.id')

curl -s -o /dev/null -w "%{http_code}" -X PATCH http://localhost:8000/api/v1/data/$ADMIN_RECORD_ID \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Hacked"}'
# 預期輸出：403
```

### TC-DATA-009 Admin 更新任意資料
✅ 預期：200
```bash
curl -s -o /dev/null -w "%{http_code}" -X PATCH http://localhost:8000/api/v1/data/$RECORD_ID \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Admin Updated"}'
# 預期輸出：200
```

### TC-DATA-010 創建者刪除自己的資料
✅ 預期：204
```bash
DEL_ID=$(curl -s -X POST http://localhost:8000/api/v1/data/ \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"To Delete","value":10.0,"category":"temperature"}' | jq -r '.id')

curl -s -o /dev/null -w "%{http_code}" -X DELETE http://localhost:8000/api/v1/data/$DEL_ID \
  -H "Authorization: Bearer $USER_TOKEN"
# 預期輸出：204
```

### TC-DATA-011 非創建者刪除資料
✅ 預期：403
```bash
curl -s -o /dev/null -w "%{http_code}" -X DELETE http://localhost:8000/api/v1/data/$ADMIN_RECORD_ID \
  -H "Authorization: Bearer $USER_TOKEN"
# 預期輸出：403
```

### TC-DATA-012 刪除不存在的資料
✅ 預期：404
```bash
curl -s -o /dev/null -w "%{http_code}" -X DELETE http://localhost:8000/api/v1/data/99999 \
  -H "Authorization: Bearer $USER_TOKEN"
# 預期輸出：404
```

### TC-DATA-013 數值超過閾值時標記異常
✅ 預期：201，`is_anomaly: true`
```bash
curl -s -X POST http://localhost:8000/api/v1/data/ \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Hot Sensor","value":90.0,"category":"temperature","threshold":80.0}' | jq '.is_anomaly'
# 預期輸出：true
```

### TC-DATA-014 CSV 批量導入
✅ 預期：201，`imported` 為匯入筆數
```bash
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/v1/data/import/csv \
  -H "Authorization: Bearer $USER_TOKEN" \
  -F "file=@sample_data.csv"
# 預期輸出：201
```

### TC-DATA-015 JSON 批量導入
✅ 預期：201，`imported: 2`
```bash
echo '[{"title":"J1","value":55.0,"category":"cpu_load"},{"title":"J2","value":70.0,"category":"memory_usage"}]' > /tmp/test.json

curl -s -X POST http://localhost:8000/api/v1/data/import/json \
  -H "Authorization: Bearer $USER_TOKEN" \
  -F "file=@/tmp/test.json" | jq '.imported'
# 預期輸出：2
```

---

## Module 4: Real-time Monitoring（即時監控）

> 需在瀏覽器 DevTools Console 手動執行（WebSocket 無法用 curl 測試）

### TC-WS-001 有效 token 建立 WebSocket 連線
```javascript
// 先取得 token（可從 TC-AUTH-001 結果複製）
ws = new WebSocket("ws://localhost:8000/ws?token=<YOUR_TOKEN>")
ws.onopen = () => console.log("Connected, readyState:", ws.readyState)
// 預期輸出：Connected, readyState: 1
```

### TC-WS-002 無效 token 建立 WebSocket 連線
```javascript
ws2 = new WebSocket("ws://localhost:8000/ws?token=invalid.token")
ws2.onclose = (e) => console.log("Closed, code:", e.code)
// 預期輸出：Closed, code: 4001
```

### TC-WS-003 連線後收到即時資料
```javascript
ws.onmessage = (e) => console.log(JSON.parse(e.data))
// 等待約 2 秒，預期 Console 顯示 { type: "realtime_data", data: {...} }
```

### TC-WS-004 即時資料格式正確
```javascript
ws.onmessage = (e) => {
  const data = JSON.parse(e.data).data
  console.log("value:", data.value, "category:", data.category,
              "is_anomaly:", data.is_anomaly, "timestamp:", data.timestamp)
}
// 預期：四個欄位均存在
```

### TC-WS-005 模擬器異常偵測
```javascript
ws.onmessage = (e) => {
  const data = JSON.parse(e.data).data
  if (data.is_anomaly) console.log("Anomaly! value:", data.value, "> threshold:", data.threshold)
}
// 預期：is_anomaly=true 時，value 必定大於 threshold
```

---

## Module 5: Analytics（資料分析）

### TC-ANA-001 取得統計摘要
✅ 預期：200，含所有統計欄位
```bash
curl -s http://localhost:8000/api/v1/analytics/ \
  -H "Authorization: Bearer $USER_TOKEN" | jq '.summary'
# 預期：total, avg_value, max_value, min_value, anomaly_count 均存在
```

### TC-ANA-002 依時間範圍統計
✅ 預期：`total >= 1`
```bash
curl -s "http://localhost:8000/api/v1/analytics/?start_time=2020-01-01T00:00:00&end_time=2099-12-31T00:00:00" \
  -H "Authorization: Bearer $USER_TOKEN" | jq '.summary.total'
# 預期輸出：>= 1
```

### TC-ANA-003 依分類統計
✅ 預期：只計算 humidity 資料
```bash
curl -s "http://localhost:8000/api/v1/analytics/?category=humidity" \
  -H "Authorization: Bearer $USER_TOKEN" | jq '.summary.total'
```

### TC-ANA-004 分類聚合資料
✅ 預期：`categories` 每項含 `category`、`count`、`avg_value`
```bash
curl -s http://localhost:8000/api/v1/analytics/ \
  -H "Authorization: Bearer $USER_TOKEN" | jq '.categories[0]'
```

### TC-ANA-005 趨勢資料（小時區間）
✅ 預期：`trend` 為陣列
```bash
curl -s "http://localhost:8000/api/v1/analytics/?trend_interval=hour" \
  -H "Authorization: Bearer $USER_TOKEN" | jq '.trend | type'
# 預期輸出："array"
```

### TC-ANA-006 趨勢資料（天區間）
✅ 預期：`trend` 為陣列
```bash
curl -s "http://localhost:8000/api/v1/analytics/?trend_interval=day" \
  -H "Authorization: Bearer $USER_TOKEN" | jq '.trend | type'
# 預期輸出："array"
```

### TC-ANA-007 匯出 Excel
✅ 預期：200，下載 xlsx 檔案
```bash
curl -s -o /tmp/export.xlsx -w "%{http_code}" \
  http://localhost:8000/api/v1/analytics/export/excel \
  -H "Authorization: Bearer $USER_TOKEN"
# 預期輸出：200，/tmp/export.xlsx 可開啟
```

### TC-ANA-008 無資料時統計摘要
✅ 預期：`total=0`，`avg_value=0`（需在空 DB 環境測試）
```bash
curl -s http://localhost:8000/api/v1/analytics/ \
  -H "Authorization: Bearer $USER_TOKEN" | jq '{total: .summary.total, avg: .summary.avg_value}'
```

---

## Module 6: Admin（系統管理）

### TC-ADM-001 Admin 取得系統日誌
✅ 預期：200，含 `items` 和 `total`
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/admin/logs \
  -H "Authorization: Bearer $ADMIN_TOKEN"
# 預期輸出：200
```

### TC-ADM-002 非 Admin 取得系統日誌
✅ 預期：403
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/admin/logs \
  -H "Authorization: Bearer $USER_TOKEN"
# 預期輸出：403
```

### TC-ADM-003 系統日誌分頁
✅ 預期：`page=1`，`size=50`
```bash
curl -s "http://localhost:8000/api/v1/admin/logs?page=1&size=50" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '{page, size}'
# 預期輸出：{"page": 1, "size": 50}
```

### TC-ADM-004 取得資料庫狀態
✅ 預期：含 `db_version` 和 `tables`
```bash
curl -s http://localhost:8000/api/v1/admin/db-status \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '{db_version, tables_count: (.tables | length)}'
```

### TC-ADM-005 登入行為寫入日誌
✅ 預期：日誌中有 `action: login`
```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin1234"}' > /dev/null

curl -s "http://localhost:8000/api/v1/admin/logs?size=100" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '[.items[].action] | contains(["login"])'
# 預期輸出：true
```

### TC-ADM-006 註冊行為寫入日誌
✅ 預期：日誌中有 `action: register`
```bash
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"logtestuser","email":"logtest@test.com","password":"password123"}' > /dev/null

curl -s "http://localhost:8000/api/v1/admin/logs?size=100" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '[.items[].action] | contains(["register"])'
# 預期輸出：true
```
