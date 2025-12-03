"""
Модуль web сервера
"""
from .server import create_app
from .handlers import (
    handle_init,
    handle_claim_bonus,
    handle_place_bet,
    handle_cashout
)

__all__ = [
    'create_app',
    'handle_init',
    'handle_claim_bonus',
    'handle_place_bet',
    'handle_cashout'
]