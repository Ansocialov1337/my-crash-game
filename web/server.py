from aiohttp import web
import aiofiles
import os

async def handle_index(request):
    """Главная страница"""
    html_path = os.path.join(os.path.dirname(__file__), 'index.html')
    async with aiofiles.open(html_path, 'r', encoding='utf-8') as f:
        html = await f.read()
    return web.Response(text=html, content_type='text/html', charset='utf-8')

async def handle_game(request):
    """Страница игры"""
    html_path = os.path.join(os.path.dirname(__file__), 'game.html')
    async with aiofiles.open(html_path, 'r', encoding='utf-8') as f:
        html = await f.read()
    return web.Response(text=html, content_type='text/html', charset='utf-8')

def create_app():
    """Создание и настройка приложения"""
    app = web.Application()
    
    # Настройка маршрутов
    app.router.add_get('/', handle_index)
    app.router.add_get('/game', handle_game)
    
    # Статические файлы
    static_path = os.path.join(os.path.dirname(__file__), 'static')
    if os.path.exists(static_path):
        app.router.add_static('/static', path=static_path)
    
    return app
