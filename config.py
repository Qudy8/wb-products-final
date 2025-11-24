"""Конфигурация бота"""
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
DB_NAME = 'bot_database.db'

# Ключ шифрования для API ключей (32 байта base64)
# Если не указан в .env, будет сгенерирован автоматически
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')

# WB API endpoints
WB_API_DISCOUNTS_URL = 'https://discounts-prices-api.wildberries.ru'
