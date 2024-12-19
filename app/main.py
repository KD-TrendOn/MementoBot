# app/main.py

import asyncio
import logging
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from .config import Config
from .handlers import register_all_handlers
from .vectorstore import init_vectorstore

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Глобальное хранилище для векторных сторах
vectorstores = None

async def on_startup(dp):
    global vectorstores
    try:
        vectorstores = await init_vectorstore()
        logger.info("Векторное хранилище инициализировано.")
    except Exception as e:
        logger.exception(f"Ошибка при инициализации векторного хранилища: {e}")
        raise

def main():
    try:
        bot = Bot(token=Config.BOT_TOKEN, parse_mode="HTML")
        storage = MemoryStorage()
        dp = Dispatcher(bot, storage=storage)

        # Добавляем Middleware для логирования
        dp.middleware.setup(LoggingMiddleware())

        # Регистрируем все обработчики
        register_all_handlers(dp)

        # Запускаем поллинг с вызовом on_startup при старте
        logger.info("Запуск бота.")
        executor.start_polling(dp, on_startup=on_startup)
    except Exception as e:
        logger.exception(f"Критическая ошибка при запуске бота: {e}")

if __name__ == '__main__':
    main()
