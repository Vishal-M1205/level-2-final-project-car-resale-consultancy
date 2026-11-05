from collections.abc import AsyncGenerator

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.core.config import config

conn_url = URL.create(
    drivername=config.database_drivername,
    username=config.database_user,
    password=config.database_password,
    host=config.database_host,
    database=config.database_name,
    port=config.database_port,
)

async_engine = create_async_engine(
    url=conn_url,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=3,
    max_overflow=10,
    pool_pre_ping=True,
)

AsyncSessionMaker = async_sessionmaker(bind=async_engine, expire_on_commit=False)


async def get_db_connection() -> AsyncGenerator[AsyncSession, None]:

    async with AsyncSessionMaker() as session:
        yield session
