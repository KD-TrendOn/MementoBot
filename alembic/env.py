# migrations/env.py

from __future__ import with_statement
import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Добавляем корневую директорию проекта в sys.path для импорта модулей
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models import Base  # Импортируйте вашу базу моделей
from app.config import Config  # Импортируйте конфигурацию

# Это объект Alembic Config, который предоставляет доступ к значениям в файле .ini
config = context.config

# Интерпретируем конфигурационный файл для настройки логирования
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Добавляем MetaData ваших моделей для автогенерации
target_metadata = Base.metadata

def get_sync_url():
    return Config.SYNC_DATABASE_URL

def run_migrations_offline():
    """Запуск миграций в офлайн режиме."""
    url = get_sync_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Запуск миграций в онлайн режиме."""
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = get_sync_url()

    connectable = engine_from_config(
        configuration,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Полезно для отслеживания изменений типов столбцов
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
