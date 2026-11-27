from typing import AsyncGenerator, Any
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from wapang.database.settings import DB_SETTINGS


class DatabaseManager:
    def __init__(self):
        url = make_url(DB_SETTINGS.url)
        async_url = url.set(
            drivername={
                "mysql": "mysql+asyncmy",
                "sqlite": "sqlite+aiosqlite",
            }[url.get_backend_name()]
        )
        self.engine = create_async_engine(
            async_url,
            pool_recycle=28000,
            pool_size=10,
            pool_pre_ping=True,
        )
        self.session_factory = async_sessionmaker(bind=self.engine, expire_on_commit=False)

database_manager = DatabaseManager()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with database_manager.session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e