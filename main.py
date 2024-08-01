import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dotenv import load_dotenv
from handlers import router
from database import create_db, drop_db, session_maker
from middlewares import DataBaseSession


async def on_startup(bot):
    # await drop_db()

    await bot.set_webhook(str(os.getenv("URL_APP")))
    await create_db()


async def on_shutdown(bot):
    await bot.delete_webhook()
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

    # Создание веб-приложения для обработки запросов
    app = web.Application()
    webhook_path = '/webhook_path'  # Указанный путь для вебхука
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=webhook_path)
    setup_application(app, dp, bot=bot)

    # Запуск веб-приложения на всех интерфейсах и порту 443
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host='0.0.0.0', port=443)
    await site.start()

    print(f"Bot is running on {os.getenv('URL_APP')}")

    # Ожидание сигнала завершения
    try:
        while True:
            await asyncio.sleep(3600)  # Keep alive
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        await runner.cleanup()

if __name__ == '__main__':
    asyncio.run(main())
