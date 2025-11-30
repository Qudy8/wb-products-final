#!/bin/bash

# Скрипт автоматической установки WB Products Bot
# Использование: bash deploy.sh

set -e

echo "🚀 Начало установки WB Products Bot..."

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Обновление системы
echo -e "${YELLOW}📦 Обновление системы...${NC}"
apt update && apt upgrade -y

# 2. Установка необходимых пакетов
echo -e "${YELLOW}📦 Установка Python и зависимостей...${NC}"
apt install -y python3 python3-pip python3-venv git curl wget unzip

# 3. Создание директории для бота
BOT_DIR="/root/wb-products-bot"
echo -e "${YELLOW}📁 Создание директории $BOT_DIR...${NC}"
mkdir -p $BOT_DIR
cd $BOT_DIR

# 4. Попытка клонирования репозитория
echo -e "${YELLOW}📥 Загрузка кода...${NC}"
if git clone https://github.com/Qudy8/wb-products-final.git .; then
    echo -e "${GREEN}✅ Репозиторий успешно клонирован${NC}"
else
    echo -e "${YELLOW}⚠️  Git clone не удался, попробуем скачать архив...${NC}"
    wget https://github.com/Qudy8/wb-products-final/archive/refs/heads/main.zip -O main.zip
    unzip -o main.zip
    mv wb-products-final-main/* .
    rm -rf wb-products-final-main main.zip
    echo -e "${GREEN}✅ Архив успешно скачан и распакован${NC}"
fi

# 5. Создание виртуального окружения
echo -e "${YELLOW}🐍 Создание виртуального окружения...${NC}"
python3 -m venv venv
source venv/bin/activate

# 6. Установка Python зависимостей
echo -e "${YELLOW}📚 Установка Python пакетов...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# 7. Создание .env файла если его нет
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚙️  Создание .env файла...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  ВАЖНО: Отредактируйте файл .env и добавьте ваши ключи!${NC}"
    echo -e "${YELLOW}    nano .env${NC}"
fi

# 8. Создание директории для пользовательских файлов
mkdir -p user_files

# 9. Создание systemd сервиса
echo -e "${YELLOW}🔧 Создание systemd сервиса...${NC}"
cat > /etc/systemd/system/wb-bot.service <<EOL
[Unit]
Description=WB Products Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$BOT_DIR
Environment="PATH=$BOT_DIR/venv/bin"
ExecStart=$BOT_DIR/venv/bin/python $BOT_DIR/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

# 10. Включение и запуск сервиса
systemctl daemon-reload
systemctl enable wb-bot

echo ""
echo -e "${GREEN}✅ Установка завершена!${NC}"
echo ""
echo -e "${YELLOW}📝 Следующие шаги:${NC}"
echo "1. Отредактируйте файл .env:"
echo "   nano $BOT_DIR/.env"
echo ""
echo "2. Запустите бота:"
echo "   systemctl start wb-bot"
echo ""
echo "3. Проверьте статус:"
echo "   systemctl status wb-bot"
echo ""
echo "4. Просмотр логов:"
echo "   journalctl -u wb-bot -f"
echo ""
