import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Импортируем наши настройки и Base, чтобы Alembic видел все модели.
# Важно: модели должны быть импортированы до вызова target_metadata,
# иначе autogenerate не увидит таблицы.
from app.core.config import settings
from app.db.base import Base
import app.db.models

# Alembic Config object — даёт доступ к значениям из alembic.ini
config = context.config

# Подставляем URL БД из наших настроек
config.set_main_option("sqlalchemy.url", settings.database_url)

# Настройка логирования Python из alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные, на которые опирается autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Offline-режим: генерирует SQL без подключения к БД."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,              # отслеживать изменения типов
        compare_server_default=True,    # отслеживать изменения дефолтов
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Online-режим: реально подключается к БД через async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()