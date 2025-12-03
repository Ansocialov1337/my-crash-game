import aiosqlite

async def create_user(user_id: int, username: str = None):
    """Создание нового пользователя"""
    async with aiosqlite.connect('bot.db') as db:
        await db.execute(
            'INSERT OR IGNORE INTO users (user_id, username, balance) VALUES (?, ?, ?)',
            (user_id, username, 1000.0)
        )
        await db.commit()

async def get_user(user_id: int):
    """Получение данных пользователя"""
    async with aiosqlite.connect('bot.db') as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            'SELECT * FROM users WHERE user_id = ?',
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def update_balance(user_id: int, amount: float):
    """Обновление баланса пользователя"""
    async with aiosqlite.connect('bot.db') as db:
        await db.execute(
            'UPDATE users SET balance = balance + ? WHERE user_id = ?',
            (amount, user_id)
        )
        await db.commit()

async def add_game(user_id: int, bet_amount: float, multiplier: float, win_amount: float):
    """Добавление записи об игре"""
    async with aiosqlite.connect('bot.db') as db:
        await db.execute(
            'INSERT INTO games (user_id, bet_amount, multiplier, win_amount) VALUES (?, ?, ?, ?)',
            (user_id, bet_amount, multiplier, win_amount)
        )
        
        # Обновляем статистику пользователя
        if win_amount > 0:
            await db.execute(
                'UPDATE users SET total_games = total_games + 1, total_won = total_won + ? WHERE user_id = ?',
                (win_amount, user_id)
            )
        else:
            await db.execute(
                'UPDATE users SET total_games = total_games + 1, total_lost = total_lost + ? WHERE user_id = ?',
                (bet_amount, user_id)
            )
        
        await db.commit()

async def get_user_stats(user_id: int):
    """Получение статистики пользователя"""
    async with aiosqlite.connect('bot.db') as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            'SELECT total_games, total_won, total_lost FROM users WHERE user_id = ?',
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None
