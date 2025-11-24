#!/bin/bash
# Скрипт для обновления бота через Git

set -e

echo "=== Git Deploy для WB Products Bot ==="

PROJECT_DIR="/opt/wbproducts"

# Переход в директорию проекта
cd $PROJECT_DIR

# Остановка бота
echo "Остановка бота..."
systemctl stop wbbot

# Получение обновлений из Git
echo "Получение обновлений из Git..."
git pull origin main || git pull origin master

# Активация виртуального окружения
echo "Активация виртуального окружения..."
source venv/bin/activate

# Установка/обновление зависимостей
echo "Обновление зависимостей..."
pip install --upgrade -r requirements.txt 2>/dev/null || pip install --upgrade aiogram aiosqlite python-dotenv openpyxl requests cryptography

# Запуск бота
echo "Запуск бота..."
systemctl start wbbot

# Проверка статуса
echo "Проверка статуса..."
sleep 2
systemctl status wbbot --no-pager

echo ""
echo "=== Деплой завершен! ==="
echo ""
echo "Смотреть логи: journalctl -u wbbot -f"
