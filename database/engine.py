# Запуск самой бд

import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.models import Base

# подтягиваем ЮРЛ базы с выводом запросов в терминал
engine = create_async_engine(os.getenv('DB_LITE'), echo=True)

# берем ссесию для запросов в БД асинхроный метод, Чтобы воспользоваться ссесией повторно
session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


# Создание всех таблиц
async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Удаление таблиц
async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)