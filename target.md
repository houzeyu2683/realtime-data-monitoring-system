題目：即時資料分析與監控系統

專案需求概述:

開發一個「即時資料分析與監控系統」，該系統需要：
1. 後端使用 FastAPI 提供 RESTful API 和 WebSocket 連接
2. 使用 Docker 和 Docker Compose 進行容器化部署
3. 前端使用 Streamlit 實現資料可視化和互動介面
4. 實現資料持久化（MariaDB，必須使用 SQLAlchemy ORM）
5. 包含但不限於使用者認證和權限管理
6. 實現即時資料推送功能

技術要求:

後端 (FastAPI):
- 使用 FastAPI 框架
- 實現 JWT 認證機制
- RESTful API 設計（CRUD 操作）
- WebSocket 即時資料推送
- 使用 SQLAlchemy ORM 操作資料庫（必須使用 ORM，禁止原生 SQL）
- 異步處理
- 資料驗證（Pydantic）
- 提供Swagger 文件
- 錯誤處理和日誌記錄
- API 需使用RestFul 格式

資料庫 (MariaDB):
- 使用 MariaDB 11.7 
- 必須使用 SQLAlchemy ORM 進行所有資料庫操作
- 資料庫遷移管理（Alembic）
- 連接池管理（SQLAlchemy Engine）
- 支援異步操作（使用asyncmy）

前端 (Streamlit):
- 使用 Streamlit 構建互動式介面
- 實現登入/登出功能
- 即時資料圖表更新
- 多頁面應用架構
- Session 狀態管理
- 與後端 API 整合

Docker:
- 撰寫 Dockerfile（多階段構建）
- Docker Compose 編排多容器
- 容器間網路通訊
- Volume 資料持久化
- 環境變數管理

功能需求:

1. 使用者管理模組
   - 使用者註冊
   - 使用者登入（JWT Token）
   - 使用者角色（Admin, User, Viewer）
   - 權限控制（不同角色不同操作權限）

2. 資料管理模組
   - 創建資料記錄（包含但不限於：標題、數值、分類、時間戳）
   - 讀取資料（支援分頁、篩選、排序）
   - 更新資料（僅限創建者或Admin）
   - 刪除資料（僅限創建者或Admin）
   - 批量導入資料（CSV/JSON）

3. 即時監控模組
   - 模擬即時資料生成器（每秒生成隨機資料）
   - WebSocket 連接推送即時資料
   - 前端即時圖表更新（折線圖、柱狀圖）
   - 資料異常告警（數值超過閾值時標記）

4. 資料分析模組
   - 統計分析（總計、平均、最大、最小值）
   - 時間範圍查詢
   - 分類資料聚合
   - 資料趨勢圖表
   - 可下載Excel

5. 系統管理模組（Admin 專用）
   - 查看所有使用者列表
   - 使用者權限管理
   - 系統日誌查詢
   - 資料庫狀態監控

提交要求:

1. 完整的專案代碼（上傳至 GitHub）
2. README.md 包含但不限於：
   - 專案介紹
   - 技術棧說明
   - 本地運行步驟
   - Docker 部署指令
   - API 文件連結
   - 測試帳號資訊
3. .env.example 文件
4. 至少一個測試資料的 CSV 範例
5. 系統架構圖