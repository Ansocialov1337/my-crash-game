"""
Главная точка входа приложения
Запускает Web сервер и Telegram бота
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher

from utils.config import BOT_TOKEN, WEBAPP_HOST, WEBAPP_PORT, WEBAPP_URL
from database.models import init_db
from bot.handlers import router as bot_router
from web.server import create_app
from aiohttp import web


async def start_web_server():
    """Запуск web сервера"""
    app = create_app()

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT)
    await site.start()

    print(f"🌐 Web сервер запущен на http://{WEBAPP_HOST}:{WEBAPP_PORT}")
    print(f"🔗 Публичный URL: {WEBAPP_URL}")


async def start_bot():
    """Запуск Telegram бота"""
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Регистрируем роутеры
    dp.include_router(bot_router)

    print("🤖 Telegram бот запущен!")

    # Запускаем polling
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


async def main():
    """Главная функция"""
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("🎮 Runner Crash Game")
    print("=" * 60)

    # Инициализация БД
    await init_db()

    # Запускаем web сервер
    await start_web_server()

    print("\n📝 Инструкция для деплоя:")
    print("1. Для локального тестирования - открой http://localhost:8080")
    print("2. Для деплоя используй Heroku/Railway/Render")
    print("3. Получи публичный URL")
    print("4. Открой @BotFather -> /myapps -> Edit Mini App")
    print("5. Укажи свой публичный URL")
    print("6. Готово!\n")

    # Запускаем бота
    await start_bot()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Приложение остановлено")
    except Exception as e:

        print(f"\n❌ Критическая ошибка: {e}")
