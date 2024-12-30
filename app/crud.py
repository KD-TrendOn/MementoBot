from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from . import models

async def create_user(db: AsyncSession, telegram_id: int, username: str = None):
    db_user = models.User(telegram_id=telegram_id, username=username)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def get_user(db: AsyncSession, telegram_id: int):
    result = await db.execute(select(models.User).where(models.User.telegram_id == telegram_id))
    return result.scalars().first()

async def update_user(db: AsyncSession, telegram_id: int, username: str):
    db_user = await get_user(db, telegram_id)
    if db_user:
        db_user.username = username
        await db.commit()
        await db.refresh(db_user)
    return db_user

async def delete_user(db: AsyncSession, telegram_id: int):
    db_user = await get_user(db, telegram_id)
    if db_user:
        await db.delete(db_user)
        await db.commit()
    return db_user

async def create_message(db: AsyncSession, user_id: int, content: str):
    db_message = models.Message(user_id=user_id, content=content)
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)
    return db_message

async def get_user_messages(db: AsyncSession, user_id: int, limit: int = 10):
    result = await db.execute(
        select(models.Message)
        .where(models.Message.user_id == user_id)
        .order_by(models.Message.timestamp.desc())
        .limit(limit)
    )
    return result.scalars().all()
