#!/bin/bash
# Скрипт деплоя WB Products Bot на сервер

set -e

echo "=== Начало деплоя WB Products Bot ==="

# Проверка Python
echo "Проверка Python..."
python3 --version || { echo "Python3 не установлен!"; exit 1; }

# Создание директории проекта
PROJECT_DIR="/opt/wbproducts"
echo "Создание директории проекта $PROJECT_DIR..."
mkdir -p $PROJECT_DIR

# Установка виртуального окружения
echo "Создание виртуального окружения..."
cd $PROJECT_DIR
python3 -m venv venv

# Активация виртуального окружения
echo "Активация виртуального окружения..."
source venv/bin/activate

# Установка зависимостей
echo "Установка зависимостей..."
pip install --upgrade pip
pip install aiogram==3.15.0 aiosqlite python-dotenv openpyxl requests

# Создание .env файла (если не существует)
if [ ! -f .env ]; then
    echo "Создание .env файла..."
    read -p "Введите токен бота: " BOT_TOKEN
    echo "BOT_TOKEN=$BOT_TOKEN" > .env
    echo ".env файл создан!"
else
    echo ".env файл уже существует, пропускаем..."
fi

# Создание systemd service файла
echo "Создание systemd service..."
cat > /etc/systemd/system/wbbot.service << 'EOF'
[Unit]
Description=WB Products Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/wbproducts
Environment="PATH=/opt/wbproducts/venv/bin"
ExecStart=/opt/wbproducts/venv/bin/python /opt/wbproducts/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузка systemd
echo "Перезагрузка systemd..."
systemctl daemon-reload

# Включение автозапуска
echo "Включение автозапуска бота..."
systemctl enable wbbot

# Запуск бота
echo "Запуск бота..."
systemctl restart wbbot

# Проверка статуса
echo "Проверка статуса бота..."
sleep 2
systemctl status wbbot --no-pager

echo ""
echo "=== Деплой завершен! ==="
echo ""
echo "Полезные команды:"
echo "  systemctl status wbbot   - проверить статус"
echo "  systemctl restart wbbot  - перезапустить"
echo "  systemctl stop wbbot     - остановить"
echo "  journalctl -u wbbot -f   - смотреть логи"
