"""
Обработчики API запросов
"""
import random
from datetime import datetime, timezone
from aiohttp import web
from typing import Dict

from utils.auth import get_user_id_from_init_data
from utils.config import CRASH_DISTRIBUTION, MIN_BET, MAX_BET
from database.queries import (
    get_user, create_user, update_balance,
    claim_bonus, save_game_result, can_claim_bonus
)

# Хранилище активных игр (в продакшене использовать Redis)
active_games: Dict[str, Dict] = {}


def generate_crash_point() -> float:
    """
    Генерация crash point с заданным распределением вероятностей

    Returns:
        Случайное значение crash point
    """
    rand = random.random()
    cumulative = 0.0

    for level, config in CRASH_DISTRIBUTION.items():
        cumulative += config['probability']
        if rand <= cumulative:
            min_val, max_val = config['range']
            crash_point = round(random.uniform(min_val, max_val), 2)
            print(f"🎲 Сгенерирован crash point: {crash_point}x (уровень: {level})")
            return crash_point

    # Fallback (не должно произойти)
    return round(random.uniform(1.01, 2.00), 2)


async def handle_init(request):
    """
    POST /api/init
    Инициализация пользователя при открытии приложения
    """
    try:
        data = await request.json()
        init_data = data.get('initData', '')

        telegram_id = get_user_id_from_init_data(init_data)

        # Получаем или создаём пользователя
        user = await get_user(telegram_id)
        if not user:
            user = await create_user(telegram_id)

        # Проверяем доступность бонуса
        can_claim, hours_left = await can_claim_bonus(telegram_id)

        response_data = {
            "success": True,
            "balance": user['balance'],
            "can_claim_bonus": can_claim,
            "next_bonus_in": hours_left,
            "total_bets": user.get('total_bets', 0),
            "total_wins": user.get('total_wins', 0),
            "total_profit": user.get('total_profit', 0)
        }

        print(f"✅ Инициализация: user={telegram_id}, balance={user['balance']}")

        return web.json_response(response_data)

    except Exception as e:
        print(f"❌ Ошибка в handle_init: {e}")
        return web.json_response({
            "success": False,
            "message": "Ошибка инициализации"
        }, status=500)


async def handle_claim_bonus(request):
    """
    POST /api/claim_bonus
    Получение ежедневного бонуса
    """
    try:
        data = await request.json()
        init_data = data.get('initData', '')

        telegram_id = get_user_id_from_init_data(init_data)

        result = await claim_bonus(telegram_id)

        if not result['success']:
            return web.json_response(result, status=400)

        return web.json_response(result)

    except Exception as e:
        print(f"❌ Ошибка в handle_claim_bonus: {e}")
        return web.json_response({
            "success": False,
            "message": "Ошибка получения бонуса"
        }, status=500)


async def handle_place_bet(request):
    """
    POST /api/place_bet
    Размещение ставки и начало игры
    """
    try:
        data = await request.json()
        init_data = data.get('initData', '')
        amount = data.get('amount', 0)

        telegram_id = get_user_id_from_init_data(init_data)

        # Валидация ставки
        if not isinstance(amount, int) or amount < MIN_BET:
            return web.json_response({
                "success": False,
                "message": f"Минимальная ставка: {MIN_BET}"
            }, status=400)

        if amount > MAX_BET:
            return web.json_response({
                "success": False,
                "message": f"Максимальная ставка: {MAX_BET}"
            }, status=400)

        # Проверяем баланс
        user = await get_user(telegram_id)
        if not user:
            return web.json_response({
                "success": False,
                "message": "Пользователь не найден"
            }, status=404)

        if amount > user['balance']:
            return web.json_response({
                "success": False,
                "message": "Недостаточно монет"
            }, status=400)

        # Списываем ставку
        new_balance = user['balance'] - amount
        await update_balance(telegram_id, new_balance)

        # Генерируем crash point
        crash_point = generate_crash_point()

        # Создаём игру
        game_id = f"{telegram_id}_{int(datetime.now().timestamp() * 1000)}"
        active_games[game_id] = {
            'telegram_id': telegram_id,
            'bet_amount': amount,
            'crash_point': crash_point,
            'started_at': datetime.now(timezone.utc).isoformat()
        }

        print(f"🎮 Игра начата: user={telegram_id}, bet={amount}, crash={crash_point}x")

        return web.json_response({
            "success": True,
            "game_id": game_id,
            "crash_point": crash_point,
            "balance": new_balance
        })

    except Exception as e:
        print(f"❌ Ошибка в handle_place_bet: {e}")
        return web.json_response({
            "success": False,
            "message": "Ошибка размещения ставки"
        }, status=500)


async def handle_cashout(request):
    """
    POST /api/cashout
    Забрать выигрыш
    """
    try:
        data = await request.json()
        init_data = data.get('initData', '')
        multiplier = data.get('multiplier', 0)

        telegram_id = get_user_id_from_init_data(init_data)

        # Валидация множителя
        if not isinstance(multiplier, (int, float)) or multiplier < 1.0:
            return web.json_response({
                "success": False,
                "message": "Неверный множитель"
            }, status=400)

        # Находим активную игру
        game = None
        game_id = None
        for gid, g in list(active_games.items()):
            if g['telegram_id'] == telegram_id:
                game = g
                game_id = gid
                break

        if not game:
            return web.json_response({
                "success": False,
                "message": "Активная игра не найдена"
            }, status=404)

        # Проверяем, не превышен ли crash point
        if multiplier > game['crash_point']:
            # Игра уже закончилась крашем
            # Сохраняем проигрыш
            await save_game_result(
                telegram_id,
                game['bet_amount'],
                game['crash_point'],
                None,  # Не успел забрать
                -game['bet_amount']
            )

            del active_games[game_id]

            return web.json_response({
                "success": False,
                "message": "Слишком поздно! Произошёл краш"
            }, status=400)

        # Рассчитываем выигрыш
        winnings = int(game['bet_amount'] * multiplier)
        profit = winnings - game['bet_amount']

        # Обновляем баланс
        user = await get_user(telegram_id)
        new_balance = user['balance'] + winnings
        await update_balance(telegram_id, new_balance)

        # Сохраняем результат
        await save_game_result(
            telegram_id,
            game['bet_amount'],
            game['crash_point'],
            multiplier,
            profit
        )

        # Удаляем игру
        del active_games[game_id]

        print(f"💰 Выигрыш: user={telegram_id}, multiplier={multiplier}x, profit={profit}")

        return web.json_response({
            "success": True,
            "winnings": winnings,
            "profit": profit,
            "balance": new_balance,
            "multiplier": multiplier
        })

    except Exception as e:
        print(f"❌ Ошибка в handle_cashout: {e}")
        return web.json_response({
            "success": False,
            "message": "Ошибка при выплате"
        }, status=500)