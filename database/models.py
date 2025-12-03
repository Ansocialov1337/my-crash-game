"""
Модели данных
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """Модель пользователя"""
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    balance: int
    last_bonus: Optional[str]
    total_bets: int
    total_wins: int
    total_profit: int
    created_at: str

    @property
    def winrate(self) -> float:
        """Процент побед"""
        if self.total_bets == 0:
            return 0.0
        return round((self.total_wins / self.total_bets) * 100, 1)


@dataclass
class GameHistory:
    """Модель истории игры"""
    id: int
    telegram_id: int
    bet_amount: int
    crash_point: float
    cashout_point: Optional[float]
    profit: int
    created_at: str

    @property
    def is_win(self) -> bool:
        """Была ли игра выигрышной"""
        return self.profit > 0


@dataclass
class ActiveGame:
    """Модель активной игры"""
    game_id: str
    telegram_id: int
    bet_amount: int
    crash_point: float
    started_at: str