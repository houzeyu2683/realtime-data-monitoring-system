import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User, UserRole

TEST_DATABASE_URL = "mysql+asyncmy://monitor_user:monitor_pass@localhost:3306/monitoring_test"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_db() -> AsyncSession:
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(autouse=True)
async def clean_db():
    yield
    async with TestSessionLocal() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    async with TestSessionLocal() as session:
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
