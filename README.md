# 即時資料分析與監控系統

即時資料分析與監控系統，支援 WebSocket 即時推送、JWT 認證、角色權限管理與資料視覺化。

## 系統架構

詳細架構圖請見 [docs/architecture.md](docs/architecture.md)

```
┌─────────────────┐     REST API      ┌──────────────────┐     asyncmy     ┌──────────────┐
│  Streamlit      │ ────────────────► │  FastAPI         │ ───────────────► │  MariaDB     │
│  Frontend       │                   │  Backend         │                  │  11.7        │
│  :8501          │ ◄──── WebSocket ── │  :8000           │                  │  :3306       │
└─────────────────┘                   └──────────────────┘                  └──────────────┘
```

## 技術棧

| 層級 | 技術 |
|------|------|
| 前端 | Streamlit 1.41, Plotly |
| 後端 | FastAPI 0.115, Uvicorn, WebSocket |
| 認證 | JWT (python-jose), bcrypt |
| ORM | SQLAlchemy 2.0 (async) |
| 資料庫 | MariaDB 11.7 + asyncmy |
| 遷移 | Alembic |
| 容器化 | Docker + Docker Compose |
| CI/CD | GitHub Actions |

## 快速開始（本地）

### 前置需求

- Docker & Docker Compose
- Git

### 1. Clone 專案

```bash
git clone <your-repo-url>
cd RealTime-Data-Monitoring-System
```

### 2. 設定環境變數

```bash
cp .env.example .env
# 編輯 .env，修改 SECRET_KEY 等敏感設定
```

### 3. 啟動服務

```bash
docker compose up -d
```

### 4. 開啟瀏覽器

- 前端：http://localhost:8501
- API 文件：http://localhost:8000/docs

## 測試帳號

| 帳號 | 密碼 | 角色 |
|------|------|------|
| admin | admin1234 | Admin |

首次啟動會自動建立 admin 帳號。其他帳號可透過前端「註冊」頁面建立。

## Docker 部署指令

```bash
# 啟動
docker compose up -d

# 查看日誌
docker compose logs -f backend

# 停止
docker compose down

# 停止並清除資料
docker compose down -v
```

## API 文件

啟動後訪問：http://localhost:8000/docs（Swagger UI）

主要端點：

| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | /api/v1/auth/register | 使用者註冊 |
| POST | /api/v1/auth/login | 登入取得 Token |
| GET | /api/v1/data/ | 資料列表（分頁/篩選/排序）|
| POST | /api/v1/data/ | 建立資料記錄 |
| POST | /api/v1/data/import/csv | 批量 CSV 導入 |
| GET | /api/v1/analytics/ | 統計分析 |
| GET | /api/v1/analytics/export/excel | 匯出 Excel |
| WS | /ws?token=<jwt> | WebSocket 即時資料 |

## 功能模組

1. **使用者管理** - 註冊、登入、三種角色（Admin/User/Viewer）
2. **資料管理** - CRUD、分頁篩選排序、CSV/JSON 批量導入
3. **即時監控** - WebSocket 每秒推送模擬資料、折線圖、異常標記
4. **資料分析** - 統計摘要、趨勢圖、分類聚合、Excel 匯出
5. **系統管理** - 使用者管理、系統日誌、資料庫狀態（Admin 專用）

## 測試資料

使用 `sample_data.csv` 匯入範例資料：

1. 登入後進入「資料管理」頁面
2. 選擇「批量導入」Tab
3. 上傳 `sample_data.csv`
