import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from handlers import router
from database import create_db, drop_db, session_maker
from middlewares import DataBaseSession


async def on_startup(bot):
    # await drop_db()

    await create_db()


async def on_shutdown(bot):
    print('бот лег')


async def main():
    load_dotenv()
    bot_token = str(os.getenv("BOT_TOKEN"))
    bot = Bot(token=bot_token)
    dp = Dispatcher(bot=bot)
    dp.include_router(router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.update.middleware(DataBaseSession(session_pool=session_maker))

    logging.basicConfig(level=logging.INFO)

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
