"""
Валидация данных от Telegram WebApp
"""
import hmac
import hashlib
import json
from urllib.parse import parse_qs
from typing import Optional, Dict
from utils.config import BOT_TOKEN


def validate_telegram_data(init_data: str) -> Optional[Dict]:
    """
    Проверяет подлинность данных от Telegram WebApp

    Args:
        init_data: Строка initData от Telegram

    Returns:
        Dict с данными пользователя или None если валидация не прошла
    """
    if not init_data:
        print("⚠️ Пустой initData - режим разработки")
        return None

    try:
        # Парсим данные
        parsed = parse_qs(init_data)

        # Получаем hash
        received_hash = parsed.get('hash', [None])[0]
        if not received_hash:
            print("❌ Hash отсутствует")
            return None

        # Формируем строку для проверки
        data_check_string_parts = []
        for key in sorted(parsed.keys()):
            if key != 'hash':
                value = parsed[key][0]
                data_check_string_parts.append(f"{key}={value}")

        data_check_string = '\n'.join(data_check_string_parts)

        # Создаём секретный ключ
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=BOT_TOKEN.encode(),
            digestmod=hashlib.sha256
        ).digest()

        # Вычисляем hash
        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()

        # Проверяем совпадение
        if calculated_hash != received_hash:
            print("❌ Hash не совпадает")
            return None

        # Извлекаем данные пользователя
        user_json = parsed.get('user', ['{}'])[0]
        user_data = json.loads(user_json)

        result = {
            'telegram_id': user_data.get('id'),
            'username': user_data.get('username'),
            'first_name': user_data.get('first_name'),
            'last_name': user_data.get('last_name'),
            'language_code': user_data.get('language_code')
        }

        print(f"✅ Валидация успешна: user_id={result['telegram_id']}")
        return result

    except Exception as e:
        print(f"❌ Ошибка валидации: {e}")
        return None


def get_user_id_from_init_data(init_data: str) -> int:
    """
    Извлекает telegram_id из initData
    В режиме разработки возвращает тестовый ID

    Args:
        init_data: Строка initData от Telegram

    Returns:
        telegram_id пользователя
    """
    user_data = validate_telegram_data(init_data)

    if user_data and user_data.get('telegram_id'):
        return user_data['telegram_id']

    # Режим разработки - тестовый пользователь
    print("⚠️ Используется тестовый пользователь ID=12345")
    return 12345