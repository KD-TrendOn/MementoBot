# app/handlers/message_handlers.py

import logging
from aiogram import types, Dispatcher
from ..utils import (
    get_or_create_user,
    add_message_to_history,
    get_message_history
)
from ..llm_graph import main_graph

# Настройка логирования
logger = logging.getLogger(__name__)

from ..utils import map_role_to_message
async def handle_text(message: types.Message):
    logger.debug(f"Получено текстовое сообщение от пользователя {message.from_user.id}: {message.text}")
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    # 1. Сохранение сообщения в историю
    await add_message_to_history(
        user_id=user.id,
        role="human",  # Роль "user" для сообщений пользователя
        content=message.text,
    )
    logger.debug(f"Сообщение пользователя {user.id} сохранено в историю.")

    # 2. Получение обновлённой истории сообщений
    message_history = await get_message_history(user.id)
    # 3. Преобразование сообщений с учётом ролей
    updated_messages = [map_role_to_message(msg) for msg in message_history[-6:]]  # последние 6 сообщений
    # 4. Добавление объектов в состояние
    state = {
        "user_id": user.id,
        "query": message.text,
        "messages": updated_messages,
        "core_memories": [],
        "recall_memories": [],
        "answer": "",
    }

    # 5. Обработка сообщения через граф
    try:
        logger.info(f"Обработка сообщения от пользователя {user.id} через основной граф.")
        result_state = await main_graph.ainvoke(state)
        response = result_state.get("answer", "Извините, произошла ошибка.")
        # 6. Отправка ответа пользователю
        await message.reply(response)
        logger.info(f"Ответ пользователю {user.id} отправлен успешно.")
    except Exception as e:
        logger.exception(f"Ошибка при обработке LLM графа для пользователя {user.id}: {e}")
        await message.reply("Произошла ошибка при обработке вашего сообщения. Попробуйте позже.")


def register_handlers(dp: Dispatcher):
    # Обработчик для текстовых сообщений
    dp.register_message_handler(handle_text, content_types=types.ContentTypes.TEXT, state="*")
