# shop-pet-project

Онлайн-маркетплейс.

## Стек

- Python 3.14, uv
- FastAPI, SQLAlchemy 2.0 async, asyncpg, Alembic
- PostgreSQL 16, Redis, Kafka

## Локальный запуск

1. Установить Python 3.14 и uv.
2. Скопировать `.env.example` → `.env` и заполнить.
3. `uv sync`
4. `uv run dev` — запуск dev-сервера с автоперезагрузкой.