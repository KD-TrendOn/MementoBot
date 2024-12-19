# app/config.py

import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    DATABASE_URL = os.getenv('DATABASE_URL')
    SYNC_DATABASE_URL = os.getenv('SYNC_DATABASE_URL')
    PGVECTOR_URL = os.getenv('PGVECTOR_URL')

    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_BASE_PROVIDER = os.getenv('OPENAI_BASE_PROVIDER')

    logger.info("Конфигурация загружена успешно.")
