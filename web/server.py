"""
Web сервер для Mini App
"""
from aiohttp import web
from pathlib import Path

from web.handlers import (
    handle_init,
    handle_claim_bonus,
    handle_place_bet,
    handle_cashout
)
from utils.config import BASE_DIR


async def handle_index(request):
    """
    GET /
    Главная страница - HTML игры
    """
    html_path = BASE_DIR / "web" / "templates" / "index.html"

    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()

        return web.Response(text=html, content_type='text/html; charset=utf-8')

    except FileNotFoundError:
        return web.Response(
            text="<h1>404 - index.html not found</h1>",
            status=404,
            content_type='text/html'
        )


async def handle_health(request):
    """
    GET /health
    Проверка здоровья сервера (для мониторинга)
    """
    return web.json_response({
        "status": "ok",
        "service": "runner-crash-game"
    })


def create_app() -> web.Application:
    """
    Создание и настройка web приложения

    Returns:
        Настроенное aiohttp приложение
    """
    app = web.Application()

    # Маршруты
    app.router.add_get('/', handle_index)
    app.router.add_get('/health', handle_health)

    # API эндпоинты
    app.router.add_post('/api/init', handle_init)
    app.router.add_post('/api/claim_bonus', handle_claim_bonus)
    app.router.add_post('/api/place_bet', handle_place_bet)
    app.router.add_post('/api/cashout', handle_cashout)

    print("✅ Web приложение создано")

    return app