# 系統架構圖

## 整體架構

```mermaid
graph TB
    subgraph Browser["使用者瀏覽器"]
        UI[Streamlit UI]
    end

    subgraph Docker["Docker Compose 環境"]
        subgraph Frontend["monitoring_frontend :8501"]
            ST[Streamlit App]
        end

        subgraph Backend["monitoring_backend :8000"]
            API[FastAPI REST API\n/api/v1/]
            WS[WebSocket\n/ws]
            SIM[Simulator\n每秒產生資料]
            AUTH[JWT 認證]
        end

        subgraph Database["db :3306"]
            DB[(MariaDB 11.7)]
        end
    end

    UI -->|HTTP| ST
    ST -->|REST API\nBearer Token| API
    ST -->|WebSocket\n?token=JWT| WS
    SIM -->|broadcast| WS
    API -->|SQLAlchemy ORM\nasyncmy| DB
    WS -->|SQLAlchemy ORM| DB
    AUTH -.->|驗證| API
    AUTH -.->|驗證| WS
```

## API 模組結構

```mermaid
graph LR
    subgraph REST["/api/v1/"]
        A[/auth\n登入 / 註冊 / 查詢自身]
        U[/users\n用戶管理 CRUD]
        D[/data\n資料記錄 CRUD\nCSV/JSON 匯入]
        AN[/analytics\n統計分析\n趨勢 / Excel 匯出]
        AD[/admin\n系統日誌\nDB 狀態]
    end

    subgraph Roles[角色權限]
        ADMIN[Admin]
        USER[User]
        VIEWER[Viewer]
    end

    ADMIN -->|全部操作| REST
    USER -->|讀寫自己的資料| D
    USER -->|讀取| AN
    VIEWER -->|唯讀| D
    VIEWER -->|唯讀| AN
    ADMIN -->|專用| AD
    ADMIN -->|專用| U
```

## 資料流（即時監控）

```mermaid
sequenceDiagram
    participant C as 前端 (Streamlit)
    participant W as WebSocket /ws
    participant S as Simulator
    participant M as ConnectionManager

    C->>W: 連線請求 ?token=JWT
    W->>W: 驗證 JWT
    W->>M: connect(websocket)
    loop 每秒
        S->>S: 生成隨機資料
        S->>M: broadcast(data)
        M->>C: send_text(JSON)
        C->>C: 更新即時圖表
    end
    C->>W: 斷線
    W->>M: disconnect(websocket)
```
