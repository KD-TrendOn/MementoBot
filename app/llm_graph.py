# app/llm_graph.py

import logging
from langgraph.graph import StateGraph, END
from .schemas.state import State
from .utils import get_memories
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from .tools.memory_tools import save_recall_memory, search_memory, store_core_memory
from sqlalchemy import update, select
from .config import Config
from .database import async_session
from .models import MessageHistory
from datetime import datetime
from .vectorstore import get_vectorstores
from .custom_nodes import CustomToolNode
import json

logger = logging.getLogger(__name__)

def create_memory_subgraph():
    memory_graph = StateGraph(State)

    prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """Вы - личный ассистент в Telegram. Ваша главная задача - эффективно управлять информацией пользователя, сохранять важные воспоминания, факты, проводить поиск и общение с пользователем.

Инструкции:
1. Анализ и сохранение личной информации:
   - Автоматически выявляйте и сохраняйте личную информацию о пользователе (имя, работа, распорядок дня и т.д.) без запроса подтверждения.
   - Используйте store_core_memory для ключевой информации и save_recall_memory для деталей.

2. Поиск и извлечение информации:
   - Используйте search_memory для поиска в сохраненных воспоминаниях.

3. Общение и взаимодействие:
   - Будьте кратким и информативным в ответах.
   - Фокусируйтесь на выполнении задач и предоставлении полезной информации.
   - Проявляйте инициативу в организации и структурировании данных пользователя.

4. Постоянное улучшение:
   - Анализируйте паттерны использования и предлагайте оптимизации в организации данных.
   - Будьте проактивны в напоминании о важных сохраненных данных, когда это уместно.

Помните: ваша цель - быть максимально полезным, эффективно управляя информацией пользователя и минимизируя необходимость в дополнительных вопросах.
Набор базовых воспоминаний:
Core - {core_memories}
Recall - {recall_memories}
Для большего понимания обстановки, дано текущее время и дата, можно использовать его для ответа или записи: {timestamp}"""),
    ("placeholder", "{messages}"),
])


    async def memory_agent(state: State):
        logger.debug("Вход в memory_agent")
        llm = ChatOpenAI(
            api_key=Config.OPENAI_API_KEY,
            base_url=Config.OPENAI_BASE_PROVIDER,
            model="gpt-4o-2024-11-20"
        )
        chain = prompt | llm.bind_tools([
            save_recall_memory,
            search_memory,
            store_core_memory
        ])

        try:
            logger.info("Вызов LLM для обработки памяти и управления объектами.")
            response = await chain.ainvoke({
                "messages": state["messages"],
                "core_memories": "\n".join(state["core_memories"]),
                "recall_memories": "\n".join(state["recall_memories"]),
                "timestamp":str(datetime.utcnow().isoformat())
            })
            logger.debug("Получен ответ от LLM в memory_agent.")
            return {"messages": response, "answer": response.content}
        except Exception as e:
            logger.exception(f"Ошибка в memory_agent: {e}")
            raise

    memory_graph.add_node("memory_agent", memory_agent)

    def route_tools(state: State) -> str:
        last_message = state["messages"][-1]
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            logger.debug("Перенаправление на узел 'tools'")
            return "tools"
        logger.debug("Завершение обработки в memory_graph.")
        return END

    # Создание узлов для инструментов памяти и управления объектами
    memory_graph.add_node("tools", CustomToolNode([save_recall_memory, search_memory, store_core_memory]))
    memory_graph.add_conditional_edges("memory_agent", route_tools)
    memory_graph.add_edge("tools", "memory_agent")

    memory_graph.set_entry_point("memory_agent")
    logger.info("memory_subgraph создан и настроен.")
    return memory_graph.compile()

memory_subgraph = create_memory_subgraph()

async def load_memories(state: State) -> State:
    logger.debug("Загрузка памяти и объектов пользователя в граф.")
    user_id = state["user_id"]
    try:
        core_memories = await get_memories(user_id)
        vectorstores = await get_vectorstores()
        user_facts_vectorstore = vectorstores["user_facts"]
        
        recall_docs = await user_facts_vectorstore.asimilarity_search(
            query=state["query"],
            k=5,
            filter=f"(langchain_metadata->>'user_id')::int = {user_id}"
        )
        recall_memories = []
        for doc in recall_docs:
            if "timestamp" in doc.metadata:
                recall_memories.append(doc.page_content + f" Timestamp:{doc.metadata['timestamp']}")
            else:
                recall_memories.append(doc.page_content)
        logger.debug("Память пользователя загружена успешно.")
    except Exception as e:
        logger.exception(f"Ошибка при загрузке памяти пользователя {user_id}: {e}")
        core_memories = []
        recall_memories = []
    return {
        "core_memories": core_memories,
        "recall_memories": recall_memories
    }

async def process_message(state: State) -> State:
    logger.debug("Начало обработки сообщения в process_message.")
    # Получаем последние 6 сообщений для контекста
    async with async_session() as session:
        try:
            result = await session.execute(
                select(MessageHistory).where(MessageHistory.user_id == state["user_id"]).order_by(MessageHistory.created_at.desc()).limit(6)
            )
            message_history = result.scalars().all()
            
            if message_history:
                messages = []
                for msg_hist in reversed(message_history):
                    messages.extend(json.loads(msg_hist.messages))
                logger.debug(f"Загружено {len(messages)} сообщений из истории для пользователя {state['user_id']}.")
            else:
                messages = []
                logger.debug(f"История сообщений пользователя {state['user_id']} пуста.")
        except Exception as e:
            logger.exception(f"Ошибка при получении истории сообщений для пользователя {state['user_id']}: {e}")
            messages = []

    # Обработка сообщения через граф памяти и управления объектами
    try:
        logger.info(f"Обработка сообщения через memory_subgraph для пользователя {state['user_id']}.")
        result = await memory_subgraph.ainvoke(state)
        logger.debug("Ответ от memory_subgraph получен.")
    except Exception as e:
        logger.exception(f"Ошибка при вызове memory_subgraph для пользователя {state['user_id']}: {e}")
        raise

    # Сохранение обновленной истории сообщений
    async with async_session() as session:
        try:
            new_message = {
                "role": "bot",
                "content": result["answer"],
                "timestamp": datetime.utcnow().isoformat()
            }
            if message_history:
                messages_list = []
                for msg_hist in message_history:
                    messages = json.loads(msg_hist.messages)
                    messages_list.extend(messages)
                messages_list.append(new_message)
                
                await session.execute(
                    update(MessageHistory)
                    .where(MessageHistory.user_id == state["user_id"])
                    .values(messages=json.dumps(messages_list), updated_at=datetime.utcnow())
                )
                logger.debug(f"Добавлено новое сообщение в существующую историю пользователя {state['user_id']}.")
            else:
                history = MessageHistory(user_id=state["user_id"], messages=json.dumps([new_message]))
                session.add(history)
                logger.debug(f"Создана новая история сообщений для пользователя {state['user_id']}.")
            
            await session.commit()
            logger.info(f"История сообщений пользователя {state['user_id']} обновлена.")
        except Exception as e:
            logger.exception(f"Ошибка при сохранении истории сообщений для пользователя {state['user_id']}: {e}")

    return result


def create_main_graph():
    graph = StateGraph(State)
    graph.add_node("load_memories", load_memories)
    graph.add_node("process_message", process_message)
    graph.set_entry_point("load_memories")
    graph.add_edge("load_memories", "process_message")
    graph.add_edge("process_message", END)
    logger.info("main_graph создан и настроен.")
    return graph.compile()

main_graph = create_main_graph()