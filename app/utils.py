# app/utils.py
from langchain_core.runnables import RunnableConfig
from .schemas.state import GraphConfig
from sqlalchemy.future import select
from .database import async_session
from .models import User
import logging
from .models import MessageHistory, Memory
from sqlalchemy import select
from .database import async_session
from datetime import datetime
import json
logger = logging.getLogger(__name__)

DEFAULT_CATALOG_NAME = "Default Catalog"

async def get_or_create_user(telegram_id: int, username: str = None) -> User:
    logger.debug(f"Получение или создание пользователя с Telegram ID {telegram_id}.")
    async with async_session() as session:
        try:
            result = await session.execute(select(User).where(User.telegram_id == telegram_id))
            user = result.scalars().first()
            if not user:
                logger.info(f"Создание нового пользователя с Telegram ID {telegram_id}.")
                user = User(telegram_id=telegram_id, username=username)
                session.add(user)
                await session.commit()
                await session.refresh(user)
                logger.info(f"Создан пользователь {telegram_id}")
            else:
                logger.debug(f"Пользователь {telegram_id} найден с ID {user.id}.")
            return user
        except Exception as e:
            logger.exception(f"Ошибка при получении или создании пользователя с Telegram ID {telegram_id}: {e}")
            raise

from sqlalchemy.orm import selectinload

async def add_message_to_history(user_id: int, role: str, content: str):
    logger.debug(f"Добавление сообщения в историю пользователя {user_id}: {role} - {content}")
    async with async_session() as session:
        try:
            history = await session.execute(select(MessageHistory).where(MessageHistory.user_id == user_id))
            history = history.scalars().first()
            
            new_message = {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat()
            }
            if history:
                messages = json.loads(history.messages)
                messages.append(new_message)
                history.messages = json.dumps(messages)
                history.updated_at = datetime.utcnow()
                logger.debug(f"Сообщение добавлено в существующую историю пользователя {user_id}.")
            else:
                history = MessageHistory(user_id=user_id, messages=json.dumps([new_message]))
                session.add(history)
                logger.debug(f"Создана новая история сообщений для пользователя {user_id}.")
            await session.commit()
            logger.info(f"История сообщений для пользователя {user_id} обновлена.")
        except Exception as e:
            logger.exception(f"Ошибка при добавлении сообщения в историю для пользователя {user_id}: {e}")

async def get_message_history(user_id: int):
    logger.debug(f"Получение истории сообщений для пользователя {user_id}.")
    async with async_session() as session:
        try:
            history = await session.execute(select(MessageHistory).where(MessageHistory.user_id == user_id))
            history = history.scalars().first()
            messages = json.loads(history.messages) if history else []
            logger.debug(f"История сообщений для пользователя {user_id} получена успешно. Количество сообщений: {len(messages)}.")
            return messages
        except Exception as e:
            logger.exception(f"Ошибка при получении истории сообщений для пользователя {user_id}: {e}")
            return []

async def get_memories(user_id: int):
    logger.debug(f"Получение памяти для пользователя {user_id}.")
    async with async_session() as session:
        try:
            memory = await session.execute(select(Memory).where(Memory.user_id == user_id))
            memory = memory.scalars().first()
            facts = json.loads(memory.facts) if memory else []
            logger.debug(f"Память для пользователя {user_id} получена: {facts}")
            return facts
        except Exception as e:
            logger.exception(f"Ошибка при получении памяти для пользователя {user_id}: {e}")
            return []

def ensure_configurable(config: RunnableConfig) -> GraphConfig:
    """Merge the user-provided config with default values."""
    configurable = config.get("configurable", {})
    logger.debug(f"Объединение конфигурации: {configurable}")
    return {
        **configurable,
        **GraphConfig(
            user_id=configurable["user_id"],
        ),
    }


from langchain_core.messages import HumanMessage, AIMessage, AnyMessage

def map_role_to_message(msg: dict) -> AnyMessage:
    """Преобразует сообщение с учетом роли."""
    role = msg.get("role", "").lower()
    content = msg.get("content", "")
    if role == "human":
        return HumanMessage(content=content)
    else:
        return AIMessage(content=content)
