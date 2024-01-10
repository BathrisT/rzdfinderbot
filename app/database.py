from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from config import get_config

_config = get_config()
_db_url = URL.create(
    drivername='postgresql+asyncpg',
    username=_config.database.user,
    password=_config.database.password,
    host=_config.database.host,
    port=_config.database.port,
    database=_config.database.name
)

# public attrs

engine = create_async_engine(url=_db_url)

async_session_maker = sessionmaker(bind=engine, class_=AsyncSession,
                                   autoflush=True, autocommit=False, expire_on_commit=False)

Base = declarative_base()


async def get_async_session():
    async with async_session_maker() as session:
        yield session
