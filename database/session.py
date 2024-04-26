import os
from enum import Enum
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_session,
    async_sessionmaker
)
from database import Base


load_dotenv()

POSTGRES_USER = str(os.getenv("POSTGRES_USER"))
POSTGRES_PASSWORD = str(os.getenv("POSTGRES_PASSWORD"))
POSTGRES_HOST = str(os.getenv("POSTGRES_HOST"))
POSTGRES_PORT = str(os.getenv("POSTGRES_PORT"))
POSTGRES_DB = str(os.getenv("POSTGRES_DB"))


DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    execution_options={"isolation_level": "AUTOCOMMIT"},
)

async_session = async_sessionmaker(
    async_engine,
    expire_on_commit=False,
    class_=AsyncSession
)


async def get_db() -> Generator:
    async with async_session() as session:
        yield session


async def create_all():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


class DBTransactionStatus(str, Enum):
    SUCCESS = 'success'
    FAIL = 'fail'
    ALREADY_EXIST = 'already in database'
    ROLLBACK = 'rollback'
    NOT_EXIST = 'not exist in database'
    NOT_ALLOWED = 'not allowed'