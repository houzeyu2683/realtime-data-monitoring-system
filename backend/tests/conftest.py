import asyncio
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from httpx_ws.transport import ASGIWebSocketTransport
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User, UserRole
from app.websocket.simulator import run_simulator

TEST_DATABASE_URL = "mysql+asyncmy://monitor_user:monitor_pass@localhost:3306/monitoring_test"


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="session")
def session_factory(test_engine):
    return async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def clean_db(session_factory):
    yield
    async with session_factory() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()


@pytest_asyncio.fixture
async def client(session_factory) -> AsyncClient:
    async def _override():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def ws_client(session_factory) -> AsyncClient:
    async def _override():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override
    task = asyncio.create_task(run_simulator())
    async with AsyncClient(transport=ASGIWebSocketTransport(app=app), base_url="ws://test") as c:
        yield c
    task.cancel()
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def db(session_factory) -> AsyncSession:
    async with session_factory() as session:
        yield session


async def _create_user(db: AsyncSession, username: str, role: UserRole) -> User:
    user = User(
        username=username,
        email=f"{username}@test.com",
        hashed_password=hash_password("password123"),
        role=role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _get_token(client: AsyncClient, username: str) -> str:
    r = await client.post("/api/v1/auth/login", json={"username": username, "password": "password123"})
    return r.json()["access_token"]


@pytest_asyncio.fixture
async def admin_user(db):
    return await _create_user(db, "admin_user", UserRole.ADMIN)


@pytest_asyncio.fixture
async def normal_user(db):
    return await _create_user(db, "normal_user", UserRole.USER)


@pytest_asyncio.fixture
async def viewer_user(db):
    return await _create_user(db, "viewer_user", UserRole.VIEWER)


@pytest_asyncio.fixture
async def admin_token(client, admin_user):
    return await _get_token(client, "admin_user")


@pytest_asyncio.fixture
async def user_token(client, normal_user):
    return await _get_token(client, "normal_user")


@pytest_asyncio.fixture
async def viewer_token(client, viewer_user):
    return await _get_token(client, "viewer_user")
