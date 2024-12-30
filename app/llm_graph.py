from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core import StrOutputParser
from .config import Config
# Инициализация модели
llm = ChatOpenAI(
    openai_api_key=Config.OPENAI_API_KEY,
    base_url=Config.OPENAI_BASE_PROVIDER,
    model_name="gpt-4o-mini"
)

# Создание шаблона промпта
prompt = ChatPromptTemplate.from_template(
    "Напиши короткое стихотворение о {topic}."
)

# Создание цепочки
chain = prompt | llm | StrOutputParser()

# Использование цепочки
result = chain.invoke({"topic":"программировании"})
print(result)
