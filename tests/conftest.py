import asyncio
from typing import Iterable

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
import sqlalchemy
from sqlalchemy import event, orm
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from wapang.main import app
from wapang.app.users.models import User
from wapang.database.common import Base
from wapang.database.settings import DB_SETTINGS
from wapang.database.connection import get_db_session
from wapang.settings import ENV
 
@pytest.fixture(autouse=True, scope="session")
def set_test_env():
    ENV = "test"


@pytest.fixture(scope="function")
def db_engine(set_test_env,tmp_path) -> Iterable[sqlalchemy.Engine]:
    url = f"sqlite+pysqlite:///{tmp_path / 'test.db'}"
    engine = sqlalchemy.create_engine(
        url,
        connect_args={"check_same_thread": False}
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)

    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine: sqlalchemy.Engine) -> Iterable[orm.Session]:
    with orm.Session(db_engine) as session:
        yield session


@pytest.fixture
def client(db_engine: sqlalchemy.Engine) -> Iterable[TestClient]:
    async_engine = create_async_engine(
        db_engine.url.set(drivername="sqlite+aiosqlite"),
        poolclass=NullPool,
    )

    @event.listens_for(async_engine.sync_engine, "connect")
    def enable_foreign_keys(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    async_session_factory = async_sessionmaker(async_engine, expire_on_commit=False)
    async def override_get_db_session():
        async with async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    app.dependency_overrides[get_db_session] = override_get_db_session
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db_session, None)
        asyncio.run(async_engine.dispose())

@pytest.fixture
def user(
    client: TestClient
) -> User:
    req = {
        "email": "test1234@snu.ac.kr",
        "password": "password123"
    }
    
    res = client.post("/api/users", json=req)
    res_json = res.json()
    
    return User(
        id=res_json["id"],
        email=res_json["email"],
        nickname=res_json.get("nickname"),
        address=res_json.get("address"),
        phone_number=res_json.get("phone_number")
    )
    
@pytest.fixture
def token(
    client: TestClient,
    user: User
) -> dict:
    req = {
        "email": "test1234@snu.ac.kr",
        "password": "password123"
    }
    res = client.post("/api/auth/tokens", json=req)
    res_json = res.json()
    
    return {
        "access_token": res_json["access_token"],
        "refresh_token": res_json["refresh_token"]
    }

@pytest.fixture
def access_token(
    token: dict
) -> str:
    return token["access_token"]
