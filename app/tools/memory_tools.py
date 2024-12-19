# app/tools/memory_tools.py

import logging
from langchain_core.tools import tool
from langchain_core.documents import Document
from ..utils import ensure_configurable
from ..database import async_session
from ..models import Memory
from ..vectorstore import get_vectorstores
from langchain_core.runnables.config import RunnableConfig
import uuid
from sqlalchemy import select
from typing import Optional
import json

logger = logging.getLogger(__name__)

@tool
async def save_recall_memory(memory: str, config: RunnableConfig, timestamp:Optional[str]) -> str:
    """Save a recall memory to the vector store.

    Args:
        memory (str): any fact about user
        timestamp (str, optional): date or time of the memory when it happened

    Returns:
        str: result
    """
    try:
        configurable = ensure_configurable(config)
        user_id = configurable["user_id"]
        
        vectorstores = await get_vectorstores()
        user_facts_vectorstore = vectorstores["user_facts"]
        if timestamp:
            doc = Document(
                page_content=memory,
                metadata={
                    "user_id": user_id,
                    "fact_id": str(uuid.uuid4()),
                    "timestamp":timestamp
                }
            )
        else:
            doc = Document(
                page_content=memory,
                metadata={
                    "user_id": user_id,
                    "fact_id": str(uuid.uuid4())
                }
            )
        
        await user_facts_vectorstore.aadd_documents([doc])
        logger.info(f"Recall память успешно сохранена для пользователя {user_id}.")
        return "Memory saved successfully"
    except Exception as e:
        return "Failed to save memory"

@tool
async def search_memory(query: str, config: RunnableConfig, top_k: int = 5) -> list[str]:
    """Search for relevant memories in the vector store

    Args:
        query (str): natural language query for relevant recall memories
        top_k (int, optional): number of results. Defaults to 5.

    Returns:
        list[str]: relevant recall memories
    """
    try:
        configurable = ensure_configurable(config)
        user_id = configurable["user_id"]
        
        vectorstores = await get_vectorstores()
        user_facts_vectorstore = vectorstores["user_facts"]
        
        results = await user_facts_vectorstore.asimilarity_search(
            query=query,
            k=top_k,
            filter=f"(langchain_metadata->>'user_id')::int = {user_id}"
        )
        memories = []
        for doc in results:
            if "timestamp" in doc.metadata:
                memories.append(doc.page_content + f" Timestamp:{doc.metadata['timestamp']}")
            else:
                memories.append(doc.page_content)
        logger.info(f"Найдено {len(memories)} recall памяти для пользователя {user_id}.")
        return memories
    except Exception as e:
        return []

@tool
async def store_core_memory(memory: str, config: RunnableConfig, index: Optional[int] = None) -> str:
    """Store a core memory.

    Args:
        memory (str): core memory to store
        index (Optional[int], optional): position of memory in the list to replace. Defaults to None.

    Returns:
        str: status of operation
    """
    try:
        configurable = ensure_configurable(config)
        user_id = configurable["user_id"]
        
        async with async_session() as session:
            result = await session.execute(select(Memory).where(Memory.user_id == user_id))
            user_memory = result.scalars().first()
            
            if user_memory:
                facts = json.loads(user_memory.facts)
                if index is not None and 0 <= index < len(facts):
                    logger.debug(f"Обновление core памяти на позиции {index} для пользователя {user_id}.")
                    facts[index] = memory
                else:
                    logger.debug(f"Добавление новой core памяти для пользователя {user_id}.")
                    facts.insert(0, memory)
                user_memory.facts = json.dumps(facts)
            else:
                logger.debug(f"Создание новой core памяти для пользователя {user_id}.")
                user_memory = Memory(user_id=user_id, facts=json.dumps([memory]))
                session.add(user_memory)
            
            await session.commit()
        
        logger.info(f"Core память успешно сохранена для пользователя {user_id}.")
        return "Core memory stored successfully"
    except Exception as e:
        return "Failed to store core memory"
