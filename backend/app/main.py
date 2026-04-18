import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import admin, analytics, auth, data, users
from app.core.logging import logger
from app.db.init_db import init_db
from app.websocket.router import router as ws_router
from app.websocket.simulator import run_simulator


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    logger.info("Starting up...")
    await init_db()
    simulator_task = asyncio.create_task(run_simulator())
    yield
    simulator_task.cancel()
    logger.info("Shutting down...")


app = FastAPI(
    title="RealTime Data Monitoring System",
    description="即時資料分析與監控系統 API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(data.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(ws_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
