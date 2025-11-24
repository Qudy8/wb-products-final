#!/bin/bash
# Скрипт обновления WB Products Bot на сервере

set -e

echo "=== Обновление WB Products Bot ==="

PROJECT_DIR="/opt/wbproducts"

# Переход в директорию проекта
cd $PROJECT_DIR

# Остановка бота
echo "Остановка бота..."
systemctl stop wbbot

# Активация виртуального окружения
echo "Активация виртуального окружения..."
source venv/bin/activate

# Установка/обновление зависимостей (если нужно)
echo "Проверка зависимостей..."
pip install --upgrade aiogram aiosqlite python-dotenv openpyxl requests cryptography

# Запуск бота
echo "Запуск бота..."
systemctl start wbbot

# Проверка статуса
echo "Проверка статуса..."
sleep 2
systemctl status wbbot --no-pager

echo ""
echo "=== Обновление завершено! ==="
echo ""
echo "Смотреть логи: journalctl -u wbbot -f"
