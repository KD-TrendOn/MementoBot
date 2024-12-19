# app/schemas/state.py

import logging
from typing import List, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

logger = logging.getLogger(__name__)

class GraphConfig(TypedDict):
    user_id: int

class State(TypedDict):
    user_id: int
    query: str
    messages: Annotated[List[AnyMessage], add_messages]
    core_memories: List[str]
    recall_memories: List[str]
    answer: str

    def __setitem__(self, key, value):
        logger.debug(f"Установлено значение '{key}' = '{value}' в State.")
        super().__setitem__(key, value)

    def __getitem__(self, key):
        value = super().__getitem__(key)
        logger.debug(f"Получено значение '{key}' = '{value}' из State.")
        return value
