"""
Модуль Telegram бота
"""
from .handlers import router
from .keyboards import get_main_keyboard, get_back_keyboard

__all__ = ['router', 'get_main_keyboard', 'get_back_keyboard']