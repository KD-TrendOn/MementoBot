import logging
from aiogram import Bot, Dispatcher, executor, types
from os import getenv
from dotenv import load_dotenv
from .database import AsyncSessionLocal
from . import crud

load_dotenv()

API_TOKEN = getenv('BOT_TOKEN')
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    async with AsyncSessionLocal() as session:
        user = await crud.get_user(session, message.from_user.id)
        if not user:
            user = await crud.create_user(session, message.from_user.id, message.from_user.username)
        await crud.create_message(session, user.id, message.text)
    await message.reply(f"Привет, {user.username}! Ваше сообщение сохранено.")

@dp.message_handler()
async def echo(message: types.Message):
    async with AsyncSessionLocal() as session:
        user = await crud.get_user(session, message.from_user.id)
        if user:
            await crud.create_message(session, user.id, message.text)
    await message.answer(f"Вы сказали: {message.text}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
