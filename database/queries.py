"""
Запросы к базе данных
"""
import aiosqlite
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List
from database.models import User, GameHistory
from utils.config import DB_PATH, DAILY_BONUS


async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Таблица пользователей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                balance INTEGER DEFAULT 0,
                last_bonus TEXT,
                total_bets INTEGER DEFAULT 0,
                total_wins INTEGER DEFAULT 0,
                total_profit INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица истории игр
        await db.execute("""
            CREATE TABLE IF NOT EXISTS game_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                bet_amount INTEGER NOT NULL,
                crash_point REAL NOT NULL,
                cashout_point REAL,
                profit INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
            )
        """)

        # Индексы для быстрого поиска
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_game_history_user 
            ON game_history(telegram_id)
        """)

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_game_history_date 
            ON game_history(created_at)
        """)

        await db.commit()
        print("✅ База данных инициализирована")


async def get_user(telegram_id: int) -> Optional[Dict]:
    """Получить пользователя по ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
                "SELECT * FROM users WHERE telegram_id = ?",
                (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def create_user(telegram_id: int, username: str = None, first_name: str = None) -> Dict:
    """Создать нового пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO users 
            (telegram_id, username, first_name, balance) 
            VALUES (?, ?, ?, 0)""",
            (telegram_id, username, first_name)
        )
        await db.commit()
        print(f"✅ Создан новый пользователь: {telegram_id}")
        return await get_user(telegram_id)


async def update_balance(telegram_id: int, new_balance: int):
    """Обновить баланс пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET balance = ? WHERE telegram_id = ?",
            (new_balance, telegram_id)
        )
        await db.commit()


async def can_claim_bonus(telegram_id: int) -> tuple[bool, int]:
    """
    Проверить, может ли пользователь получить бонус

    Returns:
        (можно_получить, часов_до_следующего)
    """
    user = await get_user(telegram_id)
    if not user:
        return True, 0

    last_bonus = user.get('last_bonus')
    if not last_bonus:
        return True, 0

    try:
        last_bonus_dt = datetime.fromisoformat(last_bonus.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        hours_passed = (now - last_bonus_dt).total_seconds() / 3600

        if hours_passed >= 24:
            return True, 0
        else:
            hours_left = int(24 - hours_passed)
            return False, hours_left
    except Exception as e:
        print(f"Ошибка проверки бонуса: {e}")
        return True, 0


async def claim_bonus(telegram_id: int) -> Dict:
    """Получить ежедневный бонус"""
    user = await get_user(telegram_id)
    if not user:
        user = await create_user(telegram_id)

    can_claim, hours_left = await can_claim_bonus(telegram_id)

    if not can_claim:
        return {
            "success": False,
            "message": f"Следующий бонус через {hours_left} ч.",
            "balance": user['balance'],
            "hours_left": hours_left
        }

    # Выдаём бонус
    new_balance = user['balance'] + DAILY_BONUS
    now = datetime.now(timezone.utc)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET balance = ?, last_bonus = ? WHERE telegram_id = ?",
            (new_balance, now.isoformat(), telegram_id)
        )
        await db.commit()

    print(f"✅ Бонус выдан: user={telegram_id}, amount={DAILY_BONUS}")

    return {
        "success": True,
        "message": f"Получено {DAILY_BONUS} монет!",
        "balance": new_balance,
        "bonus_amount": DAILY_BONUS
    }


async def save_game_result(
        telegram_id: int,
        bet_amount: int,
        crash_point: float,
        cashout_point: Optional[float],
        profit: int
):
    """Сохранить результат игры"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Сохраняем в историю
        await db.execute("""
            INSERT INTO game_history 
            (telegram_id, bet_amount, crash_point, cashout_point, profit)
            VALUES (?, ?, ?, ?, ?)
        """, (telegram_id, bet_amount, crash_point, cashout_point, profit))

        # Обновляем статистику пользователя
        if profit > 0:
            await db.execute("""
                UPDATE users 
                SET total_wins = total_wins + 1, 
                    total_bets = total_bets + 1,
                    total_profit = total_profit + ?
                WHERE telegram_id = ?
            """, (profit, telegram_id))
        else:
            await db.execute("""
                UPDATE users 
                SET total_bets = total_bets + 1,
                    total_profit = total_profit + ?
                WHERE telegram_id = ?
            """, (profit, telegram_id))

        await db.commit()

    print(f"✅ Игра сохранена: user={telegram_id}, profit={profit}")


async def get_user_stats(telegram_id: int) -> Optional[Dict]:
    """Получить статистику пользователя"""
    user = await get_user(telegram_id)

    if not user:
        return None

    winrate = 0
    if user['total_bets'] > 0:
        winrate = round((user['total_wins'] / user['total_bets']) * 100, 1)

    return {
        'balance': user['balance'],
        'total_bets': user['total_bets'],
        'total_wins': user['total_wins'],
        'total_profit': user.get('total_profit', 0),
        'winrate': winrate
    }


async def get_recent_games(telegram_id: int, limit: int = 10) -> List[Dict]:
    """Получить последние игры пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM game_history 
            WHERE telegram_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (telegram_id, limit)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_leaderboard(limit: int = 10) -> List[Dict]:
    """Получить топ игроков по балансу"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT telegram_id, username, first_name, balance, total_wins, total_bets
            FROM users 
            ORDER BY balance DESC 
            LIMIT ?
        """, (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]