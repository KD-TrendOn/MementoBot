# app/database.py

import logging
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from .config import Config

logger = logging.getLogger(__name__)

try:
    engine: AsyncEngine = create_async_engine(Config.DATABASE_URL, echo=False)
    logger.info("Асинхронный движок SQLAlchemy создан успешно.")
except Exception as e:
    logger.exception(f"Ошибка при создании движка SQLAlchemy: {e}")
    raise

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_session() -> AsyncSession:
    logger.debug("Создание новой сессии базы данных.")
    async with async_session() as session:
        yield session
