import os
from typing import Annotated, TypedDict
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage
from langgraph.graph.message import add_messages
from .config import Config

# Определение структуры состояния
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    current_task: str

# Инициализация модели
llm = ChatOpenAI(
    openai_api_key=Config.OPENAI_API_KEY,
    base_url=Config.OPENAI_BASE_PROVIDER,
    model_name="gpt-4o-mini"
)

# Определение инструментов
@tool
def search(query: str) -> str:
    """Search for information on the internet."""
    # Имитация поиска
    return f"Search results for: {query}"

@tool
def calculate(expression: str) -> str:
    """Perform a calculation."""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Error in calculation: {str(e)}"

tools = [search, calculate]

# Создание LCEL цепочки
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant. Use the provided tools when necessary. "
               "To use a tool, respond with the tool name followed by the input in parentheses, "
               "like this: search(query) or calculate(expression)."),
    ("human", "{input}"),
    ("ai", "{agent_scratchpad}")
])
chain = prompt | llm

# Определение узлов графа
async def agent(state: State):
    messages = state['messages']
    human_message = messages[-1]
    result = await chain.ainvoke({
        "input": human_message.content,
        "agent_scratchpad": "\n".join([m.content for m in messages if isinstance(m, AIMessage)])
    })
    return {
        "messages": messages + [AIMessage(content=result.content)],
        "current_task": "process_response"
    }

async def process_tools(state: State):
    messages = state['messages']
    last_message = messages[-1]
    tool_executor = ToolExecutor(tools)
    # Извлекаем название инструмента и аргументы из сообщения
    tool_call = last_message.content.split("(")
    if len(tool_call) == 2:
        tool_name, args = tool_call[0], tool_call[1].rstrip(")")
        result = await tool_executor.ainvoke({tool_name: args})
        return {
            "messages": messages + [result],
            "current_task": "agent"
        }
    else:
        return {
            "messages": messages + [AIMessage(content="Invalid tool call format")],
            "current_task": "agent"
        }

# Создание и настройка графа
workflow = StateGraph(State)

workflow.add_node("agent", agent)
workflow.add_node("process_tools", process_tools)

workflow.set_entry_point("agent")

# Определение условных переходов
def should_use_tool(state: State):
    last_message = state['messages'][-1]
    return "process_tools" if any(tool.name in last_message.content for tool in tools) else END

workflow.add_conditional_edges(
    "agent",
    should_use_tool
)

workflow.add_edge("process_tools", "agent")

app = workflow.compile()

# Использование агента
async def main():
    inputs = {
        "messages": [HumanMessage(content="Hello, can you help me calculate 15 * 7 and then search for 'Python programming'?")],
        "current_task": "agent"
    }
    async for event in app.astream(inputs):
        if 'messages' in event:
            print(event['messages'][-1].content)

import asyncio
asyncio.run(main())