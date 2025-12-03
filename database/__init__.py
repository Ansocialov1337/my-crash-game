"""
Модуль работы с базой данных
"""
from .models import User, GameHistory, ActiveGame
from .queries import (
    init_db,
    get_user,
    create_user,
    update_balance,
    claim_bonus,
    save_game_result,
    get_user_stats,
    get_recent_games,
    get_leaderboard
)

__all__ = [
    'User',
    'GameHistory',
    'ActiveGame',
    'init_db',
    'get_user',
    'create_user',
    'update_balance',
    'claim_bonus',
    'save_game_result',
    'get_user_stats',
    'get_recent_games',
    'get_leaderboard'
]