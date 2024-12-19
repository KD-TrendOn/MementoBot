# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Устанавливаем зависимости ОС, если необходимо (например, для psycopg2)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы с зависимостями
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект внутрь контейнера
COPY . .

# Устанавливаем переменные окружения (можно также использовать .env файл)
ENV PYTHONUNBUFFERED=1

# Команда запуска: сначала применяем миграции, затем запускаем бота
CMD ["sh", "-c", "alembic upgrade head && python -m app.main"]
