FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Устанавливаем переменные окружения (можно также использовать .env файл)
ENV PYTHONUNBUFFERED=1

# Команда запуска: сначала применяем миграции, затем запускаем бота
CMD ["sh", "-c", "alembic upgrade head && python -m app.main"]
