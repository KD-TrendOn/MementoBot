import logging
from aiogram import Bot, Dispatcher, executor, types
from os import getenv
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Инициализация бота и диспетчера
bot = Bot(token=getenv('BOT_TOKEN'))
dp = Dispatcher(bot)

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я простой бот. Как дела?")

# Обработчик для всех текстовых сообщений
@dp.message_handler()
async def echo(message: types.Message):
    await message.answer(f"Вы сказали: {message.text}")

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
