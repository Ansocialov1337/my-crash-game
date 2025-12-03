"""
Конфигурация проекта
"""
import os
from pathlib import Path

# Базовая директория проекта
BASE_DIR = Path(__file__).parent.parent

# Telegram Bot Token
BOT_TOKEN = "8419665265:AAFd6rmV_e7wNp1jzOAJ_Wh7vUz7PtMSv3k"

# Настройки Web сервера
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8080))
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://localhost:8080")

# База данных
DB_PATH = BASE_DIR / "game.db"

# Игровые настройки
DAILY_BONUS = 1000
MIN_BET = 1
MAX_BET = 1000000

# Распределение crash points (вероятности)
CRASH_DISTRIBUTION = {
    'low': {
        'probability': 0.70,  # 70% шанс
        'range': (1.01, 2.00)
    },
    'medium': {
        'probability': 0.20,  # 20% шанс
        'range': (2.01, 5.00)
    },
    'high': {
        'probability': 0.08,  # 8% шанс
        'range': (5.01, 10.00)
    },
    'jackpot': {
        'probability': 0.02,  # 2% шанс
        'range': (10.01, 50.00)
    }
}

# Логирование
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")