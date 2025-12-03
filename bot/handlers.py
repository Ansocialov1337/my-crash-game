"""
Обработчики команд Telegram бота
"""
from aiogram import Router, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery
from bot.keyboards import get_main_keyboard, get_back_keyboard
from database.queries import get_user_stats, get_leaderboard, create_user

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    """Команда /start - приветствие"""
    # Создаём пользователя если его нет
    await create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )

    await message.answer(
        "🎮 <b>Runner Crash Game</b>\n\n"
        "Добро пожаловать в самую динамичную crash-игру!\n\n"
        "🏃 <b>Суть игры:</b>\n"
        "• Делай ставку\n"
        "• Бегун начинает бежать\n"
        "• Множитель растёт\n"
        "• Забери выигрыш до краша!\n\n"
        "💡 <b>Чем дольше ждёшь - тем больше риск!</b>\n\n"
        "🎁 Ежедневный бонус: 1000 монет\n\n"
        "Нажми кнопку ниже, чтобы начать:",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "back")
async def callback_back(callback: CallbackQuery):
    """Кнопка назад"""
    await callback.message.edit_text(
        "🎮 <b>Runner Crash Game</b>\n\n"
        "Выбери действие:",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "stats")
async def callback_stats(callback: CallbackQuery):
    """Показать статистику"""
    stats = await get_user_stats(callback.from_user.id)

    if not stats:
        await callback.answer("Сначала сыграй хотя бы одну игру!", show_alert=True)
        return

    profit_emoji = "📈" if stats['total_profit'] >= 0 else "📉"
    profit_text = f"+{stats['total_profit']}" if stats['total_profit'] >= 0 else str(stats['total_profit'])

    await callback.message.edit_text(
        f"📊 <b>Твоя статистика:</b>\n\n"
        f"💰 Баланс: <b>{stats['balance']}</b> монет\n"
        f"{profit_emoji} Общий профит: <b>{profit_text}</b>\n\n"
        f"🎮 Всего игр: <b>{stats['total_bets']}</b>\n"
        f"🏆 Побед: <b>{stats['total_wins']}</b>\n"
        f"📈 Винрейт: <b>{stats['winrate']}%</b>",
        reply_markup=get_back_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "leaderboard")
async def callback_leaderboard(callback: CallbackQuery):
    """Показать топ игроков"""
    top_players = await get_leaderboard(10)

    if not top_players:
        await callback.answer("Таблица лидеров пуста", show_alert=True)
        return

    text = "🏆 <b>Топ-10 игроков:</b>\n\n"

    medals = ["🥇", "🥈", "🥉"]

    for i, player in enumerate(top_players, 1):
        medal = medals[i - 1] if i <= 3 else f"{i}."
        name = player.get('first_name') or player.get('username') or f"User {player['telegram_id']}"
        balance = player['balance']
        wins = player['total_wins']
        games = player['total_bets']

        text += f"{medal} <b>{name}</b>\n"
        text += f"   💰 {balance} | 🏆 {wins}/{games}\n\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_back_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery):
    """Показать помощь"""
    await callback.message.edit_text(
        "📖 <b>Подробная инструкция:</b>\n\n"
        "<b>1️⃣ Получи бонус</b>\n"
        "Каждые 24 часа ты можешь получить 1000 монет бесплатно!\n\n"
        "<b>2️⃣ Сделай ставку</b>\n"
        "• Минимум: 1 монета\n"
        "• Максимум: весь твой баланс\n"
        "• Используй быстрые ставки: 10, 50, 100, 500\n\n"
        "<b>3️⃣ Следи за множителем</b>\n"
        "Он растёт каждые 0.1 секунды\n"
        "Но может остановиться в любой момент!\n\n"
        "<b>4️⃣ Забери выигрыш</b>\n"
        "Нажми кнопку \"💸 Забрать\" до краша\n"
        "Твой выигрыш = ставка × множитель\n\n"
        "🎨 <b>Фоны меняются по мере роста:</b>\n"
        "🌤️ 1.0-2.0x: Город\n"
        "🌄 2.1-4.0x: Природа\n"
        "🌋 4.1-7.0x: Вулканы\n"
        "🌌 7.1+: Космос\n\n"
        "💡 <b>Совет:</b> Не жадничай! Лучше забрать маленький выигрыш, чем потерять всё.\n\n"
        "Удачи! 🍀",
        reply_markup=get_back_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "about")
async def callback_about(callback: CallbackQuery):
    """О игре"""
    await callback.message.edit_text(
        "ℹ️ <b>О игре Runner Crash</b>\n\n"
        "🎮 <b>Жанр:</b> Crash Game\n"
        "🎯 <b>Цель:</b> Забрать выигрыш до краша\n"
        "💰 <b>Валюта:</b> Внутриигровые монеты\n\n"
        "📊 <b>Вероятности:</b>\n"
        "• 70% - краш до 2.0x\n"
        "• 20% - краш до 5.0x\n"
        "• 8% - краш до 10.0x\n"
        "• 2% - краш до 50.0x\n\n"
        "🎁 <b>Бонусы:</b>\n"
        "• Ежедневный бонус: 1000 монет\n"
        "• Доступен каждые 24 часа\n\n"
        "🔒 <b>Честность:</b>\n"
        "Все результаты генерируются случайно\n"
        "Crash point определяется ДО начала игры\n\n"
        "👨‍💻 <b>Версия:</b> 1.0.0\n"
        "📅 <b>Дата:</b> 2024",
        reply_markup=get_back_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Команда /stats"""
    stats = await get_user_stats(message.from_user.id)

    if not stats:
        await message.answer(
            "У тебя пока нет статистики.\n"
            "Сыграй первую игру через /start"
        )
        return

    profit_emoji = "📈" if stats['total_profit'] >= 0 else "📉"
    profit_text = f"+{stats['total_profit']}" if stats['total_profit'] >= 0 else str(stats['total_profit'])

    await message.answer(
        f"📊 <b>Твоя статистика:</b>\n\n"
        f"💰 Баланс: <b>{stats['balance']}</b> монет\n"
        f"{profit_emoji} Общий профит: <b>{profit_text}</b>\n\n"
        f"🎮 Всего игр: <b>{stats['total_bets']}</b>\n"
        f"🏆 Побед: <b>{stats['total_wins']}</b>\n"
        f"📈 Винрейт: <b>{stats['winrate']}%</b>",
        parse_mode="HTML"
    )


@router.message(Command("top"))
async def cmd_top(message: types.Message):
    """Команда /top"""
    top_players = await get_leaderboard(10)

    if not top_players:
        await message.answer("Таблица лидеров пуста")
        return

    text = "🏆 <b>Топ-10 игроков:</b>\n\n"

    medals = ["🥇", "🥈", "🥉"]

    for i, player in enumerate(top_players, 1):
        medal = medals[i - 1] if i <= 3 else f"{i}."
        name = player.get('first_name') or player.get('username') or f"User {player['telegram_id']}"
        balance = player['balance']
        wins = player['total_wins']
        games = player['total_bets']

        text += f"{medal} <b>{name}</b>\n"
        text += f"   💰 {balance} | 🏆 {wins}/{games}\n\n"

    await message.answer(text, parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Команда /help"""
    await message.answer(
        "📖 <b>Доступные команды:</b>\n\n"
        "/start - Начать игру\n"
        "/stats - Моя статистика\n"
        "/top - Топ игроков\n"
        "/help - Эта справка\n\n"
        "Для игры нажми кнопку \"🎮 Играть\" в главном меню!",
        parse_mode="HTML"
    )