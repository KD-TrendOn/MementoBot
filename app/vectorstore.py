# app/vectorstore.py

import logging
from langchain_openai import OpenAIEmbeddings
from langchain_google_cloud_sql_pg.engine import PostgresEngine
from langchain_google_cloud_sql_pg.vectorstore import AsyncPostgresVectorStore
from sqlalchemy.ext.asyncio import create_async_engine
from .config import Config
import asyncio

logger = logging.getLogger(__name__)

async def init_vectorstore():
    logger.debug("Инициализация векторного хранилища.")
    try:
        engine = create_async_engine(Config.PGVECTOR_URL, echo=False)
        pg_engine = PostgresEngine.from_engine(
            engine=engine,
            loop=asyncio.get_event_loop()
        )

        embedding_service = OpenAIEmbeddings(
            api_key=Config.OPENAI_API_KEY,
            base_url=Config.OPENAI_BASE_PROVIDER,
            model="text-embedding-3-small",
            dimensions=1024
        )

        # Инициализация таблицы для пользовательских фактов
        await pg_engine.ainit_vectorstore_table(
            table_name="user_facts_vector_store",
            vector_size=embedding_service.dimensions,
            schema_name="public",
            content_column="content",
            embedding_column="embedding",
            id_column="langchain_id",
            metadata_json_column="langchain_metadata",
            overwrite_existing=True
        )
        logger.info("Таблица user_facts_vector_store инициализирована.")

        user_facts_vectorstore = await AsyncPostgresVectorStore.create(
            engine=pg_engine,
            embedding_service=embedding_service,
            table_name="user_facts_vector_store",
            schema_name="public",
            content_column="content",
            embedding_column="embedding",
            id_column="langchain_id",
            metadata_json_column="langchain_metadata"
        )
        logger.info("Векторное хранилище для пользовательских фактов создано.")

        return {
            "user_facts": user_facts_vectorstore
        }
    except Exception as e:
        logger.exception(f"Ошибка при инициализации векторного хранилища: {e}")
        raise

vectorstores = None

async def get_vectorstores():
    global vectorstores
    if vectorstores is None:
        logger.debug("Получение векторных хранилищ.")
        vectorstores = await init_vectorstore()
    else:
        logger.debug("Векторные хранилища уже инициализированы.")
    return vectorstores
