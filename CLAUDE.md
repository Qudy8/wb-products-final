# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Описание проекта

Telegram бот для управления товарами на Wildberries. Бот позволяет пользователям подключать свой WB API ключ и получать список товаров со скидками, фильтруя их по разнице между API-ценой и реальной ценой на сайте (порог 38%+).

## Запуск и разработка

### Установка зависимостей
```bash
pip install -r requirements.txt
```

### Запуск бота
```bash
python main.py
```

### Конфигурация
- Токен бота должен быть указан в файле `.env` в переменной `BOT_TOKEN`
- База данных SQLite создается автоматически при первом запуске (`bot_database.db`)

## Архитектура

### Основные модули

**main.py** - точка входа и главная логика бота:
- Использует aiogram 3.x (FSM для состояний, Router для обработчиков)
- Содержит все обработчики команд и callback-ов
- Реализует логику фильтрации товаров со скидками (>=40% разница цен)

**wb_api.py** - взаимодействие с Wildberries API:
- `get_goods_list()` - получение списка товаров через Discounts API (async)
- `get_cards_detail()` - получение реальных цен через публичное Cards API (sync-обертка с requests)
- Cards API использует `requests` с `verify=False` из-за особенностей SSL сертификатов WB

**database.py** - работа с SQLite через aiosqlite:
- Таблица `users` с полями: `user_id`, `username`, `wb_api_key`, `excel_file_path`, `excel_file_name`, `created_at`
- Методы для работы с API ключом: `set_wb_api_key()`, `get_wb_api_key()`, `has_api_key()`
- Методы для работы с Excel: `set_excel_file()`, `get_excel_file()`, `has_excel_file()`, `delete_excel_file()`
- Все операции асинхронные

**keyboards.py** - клавиатуры Telegram:
- `get_main_menu()` - адаптируется в зависимости от наличия API ключа
- `get_settings_menu()` - inline-клавиатура для настроек (API ключ + Excel файл)
- `get_cancel_keyboard()` - клавиатура отмены

**config.py** - конфигурация:
- Загружает переменные из `.env` через `python-dotenv`
- Определяет URL WB API

### Особенности логики работы с товарами

В `main.py` функция `get_products()` (строки 69-262):

1. Получает список товаров через Discounts API (до 1000 товаров)
2. Фильтрует товары со скидками (discount > 0 или разница цен)
3. Запрашивает реальные цены через Cards API для ВСЕХ товаров со скидками
4. Рассчитывает процент разницы для каждого товара
5. Собирает статистику по диапазонам процентов
6. Финальная фильтрация: оставляет только товары с разницей цен >= 38%
7. Выводит до 20 товаров с максимальной разницей цен
8. Выводит сравнение цен: базовая → со скидкой (API) → реальная (сайт)

### Структура данных WB API

**Discounts API** (`/api/v2/list/goods/filter`):
- Возвращает структуру: `data.data.listGoods[]`
- Каждый товар: `nmID`, `discount`, `sizes[].price`, `sizes[].discountedPrice`

**Cards API** (`https://card.wb.ru/cards/v2/detail`):
- Возвращает: `data.products[]`
- Цена в `sizes[0].price.product` (в копейках * 100)

## API Endpoints используемые

1. **Discounts API** (требует авторизацию):
   - URL: `https://discounts-prices-api.wildberries.ru/api/v2/list/goods/filter`
   - Метод: GET
   - Параметры: `limit`, `offset`
   - Header: `Authorization: <WB_API_KEY>`

2. **Cards API** (публичное):
   - URL: `https://card.wb.ru/cards/v2/detail`
   - Метод: GET
   - Параметры: `appType=1`, `curr=rub`, `dest=-1257786`, `spp=30`, `nm=<id1;id2;id3>`

## Работа с Excel файлами

- Пользователи могут загружать Excel файлы (.xlsx, .xls) через настройки
- Файлы сохраняются в папку `user_files/` с префиксом `{user_id}_`
- Информация о файле хранится в БД (путь и имя файла)
- Обработчики: `upload_excel`, `show_excel_file`, `delete_excel_file`
- FSM состояние: `UploadExcel.waiting_for_file`

### Структура Excel файла:
- **Столбец A**: Категория (например, "Одежда")
- **Столбец B**: Предмет (например, "Лонгсливы")
- **Столбец C**: FBS комиссия (например, "15%")

### Логика работы с Excel:
1. При получении товаров бот загружает Excel файл пользователя
2. Для каждого товара ищет совпадение `entity` (из WB API) со столбцом B
3. При совпадении извлекает: Категорию (A), Предмет (B), FBS комиссию (C)
4. Выводит информацию в формате: **"Категория → Предмет"**

**Модуль**: `excel_helper.py` - содержит класс `ExcelHelper` для работы с Excel

## Безопасность

- API ключи хранятся в базе данных в открытом виде
- При показе пользователю ключ маскируется (первые 10 + последние 10 символов)
- Excel файлы хранятся локально в папке `user_files/`
- `.env`, `bot_database.db` и `user_files/` должны быть в `.gitignore`
