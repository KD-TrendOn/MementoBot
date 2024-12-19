# app/custom_nodes.py

from typing import Sequence, Dict, Any
from langchain_core.tools import BaseTool
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.prebuilt.tool_executor import ToolExecutor
from langchain_core.runnables import RunnableConfig

class CustomToolNode:
    def __init__(self, tools: Sequence[BaseTool]):
        self.tool_executor = ToolExecutor(tools)
        self.tools_by_name = {tool.name: tool for tool in tools}

    async def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        messages = state.get("messages", [])
        if not messages or not isinstance(messages[-1], AIMessage):
            raise ValueError("Last message must be an AIMessage")

        last_message = messages[-1]
        if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
            return state

        result = []
        for tool_call in last_message.tool_calls:
            if tool_call["name"] not in self.tools_by_name:
                result.append(ToolMessage(
                    content=f"{tool_call['name']} is not a valid tool, try one of {list(self.tools_by_name.keys())}.",
                    tool_call_id=tool_call["id"]
                ))
                continue

            # Создаем config для каждого вызова инструмента
            tool_config: RunnableConfig = {
                "configurable": {
                    "user_id": state["user_id"]
                }
            }
            
            # Добавляем config к аргументам инструмента
            tool_args = tool_call["args"]

            try:
                # Вызываем инструмент с обновленными аргументами
                observation = await self.tools_by_name[tool_call["name"]].ainvoke(tool_args,config=tool_config)
                
                result.append(ToolMessage(content=str(observation), tool_call_id=tool_call["id"]))
            except Exception as e:
                # Обработка ошибок инструмента
                result.append(ToolMessage(
                    content=f"Error in tool {tool_call['name']}: {str(e)}",
                    tool_call_id=tool_call["id"],
                    status="error"
                ))

        return {"messages": result}
