"""Основной файл Telegram бота для работы с Wildberries API"""
import asyncio
import logging
import os
import html
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from config import BOT_TOKEN
from database import Database
from wb_api import WildberriesAPI
from excel_helper import ExcelHelper
from keyboards import (
    get_main_menu,
    get_settings_menu,
    get_cancel_keyboard,
    get_api_keys_menu,
    get_api_keys_list_keyboard,
    get_key_actions_keyboard,
    get_confirm_delete_keyboard,
    get_pagination_keyboard,
    get_subscription_menu,
    get_subscription_status_keyboard,
    get_payment_methods_keyboard,
    get_card_actions_keyboard,
    get_confirm_unbind_card_keyboard,
    get_subscription_with_cards_keyboard
)
from yukassa_payment import YuKassaPayment
from config import SUBSCRIPTION_PLANS

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# Инициализация базы данных
db = Database()

# Хранилище для результатов пагинации (user_id -> {pages, current_page, key_results})
pagination_storage = {}


# Состояния для FSM
class SetApiKey(StatesGroup):
    waiting_for_key = State()


class UploadExcel(StatesGroup):
    waiting_for_file = State()


class AddApiKey(StatesGroup):
    waiting_for_name = State()
    waiting_for_key = State()


class EditApiKeyName(StatesGroup):
    waiting_for_name = State()


class EditApiKeyValue(StatesGroup):
    waiting_for_key = State()


class SetThreshold(StatesGroup):
    waiting_for_threshold = State()


# Обработчик команды /start
@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработка команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username

    await db.add_user(user_id, username)
    has_key = await db.has_api_key(user_id)

    # Проверяем активную подписку
    subscription = await db.get_active_subscription(user_id)

    # Если подписки нет, пытаемся дать пробную
    if not subscription:
        trial_created = await db.create_trial_subscription(user_id)
        if trial_created:
            # Пробная подписка успешно создана
            subscription = await db.get_active_subscription(user_id)
            await message.answer(
                "🎉 Добро пожаловать в WB Management Bot!\n\n"
                "✨ Вам активирован пробный период на 1 день!\n\n"
                "Доступные функции:\n"
                "📦 Получение списка товаров с ценами и скидками\n"
                "📊 Загрузка Excel файла с категориями\n"
                "⚙️ Настройка API ключей\n"
                "💳 Управление подпиской\n\n"
                "После окончания пробного периода для продолжения работы необходимо оформить подписку.",
                reply_markup=get_main_menu(True)  # У пользователя теперь есть подписка
            )
            return

    # У пользователя есть активная подписка
    if subscription:
        from datetime import datetime
        end_date = datetime.fromisoformat(subscription['end_date'])
        days_left = (end_date - datetime.now()).days + 1

        plan_name = "Пробный период" if subscription['plan_id'] == 'trial' else SUBSCRIPTION_PLANS.get(subscription['plan_id'], {}).get('name', 'Неизвестный план')

        await message.answer(
            f"👋 С возвращением!\n\n"
            f"📋 Подписка: {plan_name}\n"
            f"⏰ Осталось дней: {days_left}\n\n"
            "Доступные функции:\n"
            "📦 Получение списка товаров с ценами и скидками\n"
            "📊 Загрузка Excel файла с категориями\n"
            "⚙️ Настройка API ключей\n"
            "💳 Управление подпиской",
            reply_markup=get_main_menu(True)  # У пользователя есть активная подписка
        )
    else:
        # Пробный период уже был использован, нужна оплата
        await message.answer(
            "👋 Добро пожаловать в WB Management Bot!\n\n"
            "⚠️ У вас нет активной подписки.\n\n"
            "Этот бот работает по подписке. Для доступа к функциям необходимо оформить подписку.\n\n"
            "Нажмите '💳 Подписка' для выбора тарифного плана.",
            reply_markup=get_main_menu(False)  # Нет активной подписки
        )


# Обработчик кнопки "Настройки"
@router.message(F.text == "⚙️ Настройки")
async def settings_menu(message: Message):
    """Отображение меню настроек"""
    user_id = message.from_user.id

    # Проверка активной подписки
    if not await db.has_active_subscription(user_id):
        await message.answer(
            "⚠️ Для доступа к настройкам необходима активная подписка.\n\n"
            "Нажмите '💳 Подписка' для оформления.",
            reply_markup=get_main_menu(False)
        )
        return

    use_default_keys = await db.get_use_default_keys(user_id)

    await message.answer(
        "⚙️ Настройки бота\n\n"
        "Выберите раздел для настройки:",
        reply_markup=get_settings_menu(use_default_keys)
    )


# Обработчик кнопки "Список товаров"
@router.message(F.text == "📦 Список товаров")
async def get_products(message: Message):
    """Получение списка товаров по всем активным ключам (включая дефолтные)"""
    user_id = message.from_user.id

    # Проверка активной подписки
    if not await db.has_active_subscription(user_id):
        await message.answer(
            "⚠️ Для доступа к этой функции необходима активная подписка.\n\n"
            "Нажмите '💳 Подписка' для оформления.",
            reply_markup=get_main_menu(False)
        )
        return

    # Получаем все активные ключи (пользовательские + дефолтные)
    active_keys = await db.get_active_api_keys_with_defaults(user_id)

    if not active_keys:
        await message.answer(
            "⚠️ API ключи не настроены. Обратитесь к администратору.",
            reply_markup=get_main_menu(False)
        )
        return

    # Считаем ключи для сообщения
    user_keys_count = len([k for k in active_keys if not k.get('is_default', False)])
    default_keys_count = len([k for k in active_keys if k.get('is_default', False)])
    total_keys = len(active_keys)

    # Сообщение показывает общее количество ключей (пользовательские + дефолтные)
    await message.answer(f"⏳ Обрабатываю {total_keys} активных ключей...")

    # Получаем порог скидки пользователя
    user_threshold = await db.get_discount_threshold(user_id)
    logger.info(f"Порог скидки пользователя {user_id}: {user_threshold}%")

    # Загружаем Excel файл пользователя (если есть)
    excel_helper = None
    excel_file_data = await db.get_excel_file(user_id)
    if excel_file_data:
        excel_path, excel_name = excel_file_data
        if os.path.exists(excel_path):
            try:
                excel_helper = ExcelHelper(excel_path)
                stats = excel_helper.get_stats()
                logger.info(f"Excel загружен: {stats}")
            except Exception as e:
                logger.error(f"Ошибка загрузки Excel: {e}")

    # Обрабатываем каждый ключ
    all_key_results = []
    user_key_idx = 0  # Счетчик для пользовательских ключей

    for key_data in active_keys:
        key_name = key_data['name']
        api_key = key_data['key']
        is_default = key_data.get('is_default', False)

        # Показываем прогресс только для пользовательских ключей
        if not is_default:
            user_key_idx += 1
            await message.answer(f"🔑 Обрабатываю ключ {user_key_idx}/{user_keys_count}: '{key_name}'...")

        # Вызываем функцию обработки одного ключа
        key_result = await process_single_key(api_key, key_name, excel_helper, user_threshold)

        if key_result:
            key_result['is_default'] = is_default  # Помечаем результат
            all_key_results.append(key_result)
            logger.info(f"Ключ '{key_name}' (default={is_default}): найдено {len(key_result['unique_goods'])} уникальных товаров")
        else:
            # Добавляем пустой результат для этого ключа
            logger.info(f"Ключ '{key_name}' (default={is_default}): товары не найдены")
            all_key_results.append({
                'key_name': key_name,
                'stats_text': '',
                'unique_goods': [],
                'product_info': {},
                'real_prices': {},
                'goods_with_discount': 0,
                'goods_filtered': 0,
                'no_results': True,  # Флаг что результатов нет
                'is_default': is_default
            })

    # Сохраняем результаты для пагинации (одна страница = один ключ)
    pagination_storage[user_id] = {
        'results': all_key_results,
        'current_page': 0
    }

    # Показываем первую страницу
    await show_page(message, user_id, 0)


def format_price(price: float) -> str:
    """Форматирует цену: если копейки .00, то не показываем их"""
    if price == int(price):
        return f"{int(price)}"
    else:
        return f"{price:.2f}"


async def process_single_key(api_key: str, key_name: str, excel_helper, threshold: int = 28):
    """Обработка одного API ключа"""

    wb_api = WildberriesAPI(api_key)
    result = await wb_api.get_goods_list(limit=1000)

    if not result['success']:
        logger.error(f"Ошибка для ключа '{key_name}': {result['error']}")
        return None

    data = result['data']
    goods = data.get('data', {}).get('listGoods', [])

    if not goods:
        logger.info(f"Ключ '{key_name}': список товаров пуст")
        return None

    # Берем ВСЕ товары (не фильтруем по скидкам)
    logger.info(f"Ключ '{key_name}': всего товаров {len(goods)}")

    # Логируем первые 3 товара для отладки
    if goods:
        logger.info(f"Ключ '{key_name}': примеры товаров nmID={[g.get('nmID') for g in goods[:3]]}")

    if not goods:
        logger.warning(f"Ключ '{key_name}': список товаров пуст после получения от API")
        return None

    # Получаем реальные цены с сайта WB для ВСЕХ товаров
    nm_ids = [product.get('nmID') for product in goods if product.get('nmID')]

    cards_result = await wb_api.get_cards_detail(nm_ids)

    # Создаем словари для быстрого поиска цен и информации о товарах по nmId
    real_prices = {}
    product_info = {}  # Словарь для хранения категории, предмета, бренда
    cards_debug = f"Запрошено ID: {len(nm_ids)} шт ({nm_ids[:3]}...)"

    if not cards_result.get('success'):
        error_msg = cards_result.get('error', 'Unknown')
        cards_debug = f"❌ Ошибка: {error_msg[:150]}"
    elif not cards_result.get('data'):
        cards_debug = "❌ Нет данных в ответе"
    else:
        response_data = cards_result.get('data', {})

        # Логируем полную структуру для отладки
        logger.info(f"Cards API v4 структура ответа: ключи={list(response_data.keys())}")

        # Cards API v4 возвращает {'products': [...]}
        if 'products' in response_data:
            # Прямой доступ: data.products
            products = response_data.get('products', [])
            cards_debug = f"✅ Товаров получено: {len(products)}"
            received_ids = []

            for card in products:
                nm_id = card.get('id')
                if nm_id:
                    received_ids.append(nm_id)

                # В v4 API цена находится в sizes[0].price
                sizes = card.get('sizes', [])
                if sizes and len(sizes) > 0:
                    price_data = sizes[0].get('price', {})
                    # product - цена со скидкой на сайте, basic - базовая цена
                    product_price = price_data.get('product', 0)
                    basic_price = price_data.get('basic', product_price)

                    if nm_id and product_price > 0:
                        # Цена в формате копейки * 100, делим на 100 для получения рублей
                        real_prices[nm_id] = {
                            'real': product_price / 100,
                            'basic': basic_price / 100
                        }

                # Сохраняем информацию о предмете, категории и бренде
                if nm_id:
                    entity = card.get('entity', '')
                    product_info[nm_id] = {
                        'entity': entity,  # Предмет
                        'brand': card.get('brand', ''),    # Бренд
                        'name': card.get('name', ''),      # Наименование товара
                        'subject_id': card.get('subjectId', ''),
                        'subject_parent_id': card.get('subjectParentId', '')  # ID категории
                    }

                    # Ищем соответствие в Excel файле
                    if excel_helper and entity:
                        excel_data = excel_helper.find_by_subject(entity)
                        if excel_data:
                            product_info[nm_id]['excel_category'] = excel_data['category']
                            product_info[nm_id]['excel_subject'] = excel_data['subject']
                            product_info[nm_id]['excel_commission_wb'] = excel_data.get('commission_wb', '')
                            product_info[nm_id]['excel_commission_fbs'] = excel_data.get('commission_fbs', '')
                            product_info[nm_id]['excel_commission_self'] = excel_data.get('commission_self', '')

            # Отладка: показываем первые ID
            if received_ids:
                cards_debug += f" | ID: {received_ids[:3]}..."
            cards_debug += f" | Цен: {len(real_prices)}"
        else:
            cards_debug = f"❌ Нет ключа 'products'. Ключи: {list(response_data.keys())[:5]}"

    # Логируем информацию о получении цен
    logger.info(f"Ключ '{key_name}': всего товаров {len(goods)}, получено цен {len(real_prices)}")
    logger.info(f"Cards API debug: {cards_debug}")

    # Собираем статистику по процентам и фильтруем товары
    goods_to_show_filtered = []
    all_percentages = []  # Для статистики
    debug_count = 0  # Для отладки первых 5 товаров
    skipped_no_price = 0  # Счетчик товаров без цены
    skipped_zero_price = 0  # Счетчик товаров с нулевой ценой

    for product in goods:
        nm_id = product.get('nmID')
        if nm_id not in real_prices:
            skipped_no_price += 1
            continue

        # Получаем скидку продавца из Discounts API
        seller_discount = product.get('discount', 0)

        # Получаем цены из Cards API
        price_data = real_prices.get(nm_id)
        if not price_data:
            continue

        real_price = price_data['real']  # Цена на сайте
        basic_price = price_data['basic']  # Базовая цена

        if basic_price <= 0:
            skipped_zero_price += 1
            continue

        # Рассчитываем скидку на сайте (в процентах)
        site_discount = ((basic_price - real_price) / basic_price) * 100

        # Рассчитываем реальную скидку: скидка_сайта - скидка_продавца
        real_discount = site_discount - seller_discount

        # Детальное логирование для первых 5 товаров
        if debug_count < 5:
            logger.info(
                f"Товар {nm_id}: basic={basic_price:.2f}₽, real={real_price:.2f}₽, "
                f"site_discount={site_discount:.1f}%, seller_discount={seller_discount}%, "
                f"real_discount={real_discount:.1f}%"
            )
            debug_count += 1

        # Сохраняем для статистики
        all_percentages.append((real_discount, nm_id))

        # Фильтруем товары с реальной скидкой >= порога пользователя
        if real_discount >= threshold:
            goods_to_show_filtered.append(product)

    # Сортируем товары по проценту разницы (от большего к меньшему)
    all_percentages.sort(reverse=True)

    # Логируем статистику пропущенных товаров
    logger.info(
        f"Ключ '{key_name}': пропущено без цены={skipped_no_price}, "
        f"с нулевой ценой={skipped_zero_price}, обработано={len(all_percentages)}"
    )

    # Формируем статистику
    stats_text = "\n📊 Статистика по реальным скидкам (скидка сайта - скидка продавца):\n"

    if all_percentages:
        # Распределение по диапазонам
        ranges = {
            '50%+': 0,
            '45-49%': 0,
            '40-44%': 0,
            '38-39%': 0,
            '35-37%': 0,
            '30-34%': 0,
            '25-29%': 0,
            '20-24%': 0,
            '15-19%': 0,
            '10-14%': 0,
            '<10%': 0
        }

        for pct, _ in all_percentages:
            if pct >= 50:
                ranges['50%+'] += 1
            elif pct >= 45:
                ranges['45-49%'] += 1
            elif pct >= 40:
                ranges['40-44%'] += 1
            elif pct >= 38:
                ranges['38-39%'] += 1
            elif pct >= 35:
                ranges['35-37%'] += 1
            elif pct >= 30:
                ranges['30-34%'] += 1
            elif pct >= 25:
                ranges['25-29%'] += 1
            elif pct >= 20:
                ranges['20-24%'] += 1
            elif pct >= 15:
                ranges['15-19%'] += 1
            elif pct >= 10:
                ranges['10-14%'] += 1
            else:
                ranges['<10%'] += 1

        stats_text += f"Всего товаров с ценами: {len(all_percentages)}\n\n"
        for range_name, count in ranges.items():
            if count > 0:
                stats_text += f"  {range_name}: {count} шт\n"

        # Топ-5 товаров с максимальной реальной скидкой
        stats_text += f"\nТоп-5 товаров с максимальной реальной скидкой:\n"
        for i, (pct, nm_id) in enumerate(all_percentages[:5], 1):
            stats_text += f"  {i}. nmID {nm_id}: {pct:.1f}%\n"

        stats_text += "\n"

    logger.info(f"Ключ '{key_name}': после фильтра ≥{threshold}% осталось {len(goods_to_show_filtered)} товаров")

    if not goods_to_show_filtered:
        logger.warning(f"Ключ '{key_name}': нет товаров после фильтрации по порогу {threshold}%")
        logger.info(f"Ключ '{key_name}': топ-5 скидок до фильтрации: {[(pct, nm_id) for pct, nm_id in all_percentages[:5]]}")
        return None

    # Фильтруем дубликаты по категории+предмету
    unique_goods = []
    seen_categories = set()

    for product in goods_to_show_filtered:
        nm_id = product.get('nmID')
        if nm_id and nm_id in product_info:
            info = product_info[nm_id]
            # Создаем ключ "категория|предмет"
            if info.get('excel_category') and info.get('excel_subject'):
                category_key = f"{info['excel_category']}|{info['excel_subject']}"
            elif info.get('entity'):
                category_key = f"no_category|{info['entity']}"
            else:
                category_key = f"unknown|{nm_id}"

            # Добавляем только если такой пары еще не было
            if category_key not in seen_categories:
                seen_categories.add(category_key)
                unique_goods.append(product)

    logger.info(f"Ключ '{key_name}': уникальных товаров {len(unique_goods)}")

    # Возвращаем результат
    return {
        'key_name': key_name,
        'stats_text': stats_text,
        'unique_goods': unique_goods,
        'product_info': product_info,
        'real_prices': real_prices,
        'total_goods': len(goods),
        'goods_filtered': len(goods_to_show_filtered),
        'threshold': threshold
    }


async def show_page(message_or_callback, user_id: int, page: int):
    """Показывает страницу результатов"""

    if user_id not in pagination_storage:
        if isinstance(message_or_callback, Message):
            await message_or_callback.answer("📦 Нет сохраненных результатов. Запустите поиск заново.")
        else:
            await message_or_callback.message.answer("📦 Нет сохраненных результатов. Запустите поиск заново.")
        return

    storage = pagination_storage[user_id]
    all_results = storage['results']

    if page < 0 or page >= len(all_results):
        if isinstance(message_or_callback, Message):
            await message_or_callback.answer("❌ Страница не найдена")
        else:
            await message_or_callback.message.answer("❌ Страница не найдена")
        return

    result = all_results[page]

    # Формируем сообщение для этого ключа
    is_default = result.get('is_default', False)

    # Для дефолтных ключей не показываем название
    if not is_default:
        text = f"🔑 Ключ: {result['key_name']}\n"
    else:
        text = ""

    text += f"Страница {page + 1}/{len(all_results)}\n\n"

    # Проверяем есть ли результаты
    if result.get('no_results'):
        text += "⚠️ Нет товаров, подходящих по критериям\n\n"
        text += "Возможные причины:\n"
        text += "  • Нет товаров в личном кабинете\n"
        text += f"  • Все товары отфильтрованы по критерию реальной скидки ≥{result.get('threshold', 28)}%\n"
    else:
        # Статистика убрана для компактности
        # text += result['stats_text']

        # Показываем ВСЕ товары (убираем ограничение [:20])
        goods_to_display = result['unique_goods']

        text += f"📦 Товары (всего: {result['total_goods']}, подходит по критерию ≥{result.get('threshold', 28)}%: {result['goods_filtered']}, показано: {len(goods_to_display)})\n\n"

        # Отображаем товары только если они есть
        for i, product in enumerate(goods_to_display, 1):
            nm_id = product.get('nmID', 'N/A')

            # Получаем скидку продавца из Discounts API
            seller_discount = product.get('discount', 0)

            # Получаем информацию о товаре
            info = result['product_info'].get(nm_id, {}) if nm_id != 'N/A' else {}

            # Формируем заголовок товара
            text += f"{i}. "

            # Если есть данные из Excel - показываем Категория → Предмет
            if info.get('excel_category') and info.get('excel_subject'):
                text += f"{info['excel_category']} → {info['excel_subject']}\n"
            elif info.get('entity'):
                text += f"📂 {info['entity']}\n"
            else:
                text += f"Артикул: {nm_id}\n"

            # Наименование товара
            if info.get('name'):
                text += f"   📝 {info['name']}\n"

            # Рассчитываем реальную скидку и показываем только СПП
            if nm_id != 'N/A':
                price_data = result['real_prices'].get(nm_id)
                if price_data:
                    real_price = price_data['real']
                    basic_price = price_data['basic']

                    if basic_price > 0:
                        # Рассчитываем скидку на сайте
                        site_discount = ((basic_price - real_price) / basic_price) * 100
                        # СПП (скидка постоянного покупателя)
                        real_discount = site_discount - seller_discount

                        text += f"   ✅ СПП: {real_discount:.1f}%\n"

            # Показываем FBO комиссию из Excel (если есть)
            if info.get('excel_commission_wb'):
                text += f"   💼 FBO комиссия: {info['excel_commission_wb']}\n"

            # Показываем FBS комиссию из Excel (если есть)
            if info.get('excel_commission_fbs'):
                text += f"   💼 FBS комиссия: {info['excel_commission_fbs']}\n"

            text += "\n"

    # Отправляем или редактируем сообщение
    # Для дефолтных ключей не передаем название
    key_name_to_show = None if is_default else result['key_name']
    keyboard = get_pagination_keyboard(page, len(all_results), key_name_to_show)

    # Проверяем тип объекта
    if isinstance(message_or_callback, CallbackQuery):
        # Это callback от кнопки - редактируем сообщение
        try:
            await message_or_callback.message.edit_text(text, reply_markup=keyboard)
        except Exception as e:
            # Если не получилось отредактировать, отправляем новое
            await message_or_callback.message.answer(text, reply_markup=keyboard)
    else:
        # Это обычное сообщение (Message) - отправляем новое
        await message_or_callback.answer(text, reply_markup=keyboard)

    pagination_storage[user_id]['current_page'] = page


#  Обработчик пагинации
@router.callback_query(F.data.startswith("page:"))
async def pagination_handler(callback: CallbackQuery):
    """Обработчик кнопок пагинации"""
    user_id = callback.from_user.id

    # Проверка активной подписки
    if not await db.has_active_subscription(user_id):
        await callback.answer("⚠️ Необходима активная подписка", show_alert=True)
        return

    page = int(callback.data.split(":")[1])

    await show_page(callback, user_id, page)
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery):
    """Обработчик для кнопок-заглушек"""
    await callback.answer()


# Обработчик установки API ключа
@router.callback_query(F.data == "set_api_key")
async def set_api_key_start(callback: CallbackQuery, state: FSMContext):
    """Начало процесса установки API ключа"""
    await callback.message.answer(
        "🔑 Отправьте ваш WB API ключ\n\n"
        "Получить ключ можно в личном кабинете Wildberries:\n"
        "Настройки → Доступ к API → Создать новый токен\n\n"
        "⚠️ Внимание: ключ должен иметь права на:\n"
        "• Цены и скидки - Просмотр",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(SetApiKey.waiting_for_key)
    await callback.answer()


# Обработчик получения API ключа
@router.message(SetApiKey.waiting_for_key, F.text != "❌ Отмена")
async def set_api_key_process(message: Message, state: FSMContext):
    """Сохранение API ключа"""
    api_key = message.text.strip()
    user_id = message.from_user.id

    # Простая валидация
    if len(api_key) < 20:
        await message.answer("❌ Ключ слишком короткий. Проверьте правильность ввода.")
        return

    await db.set_wb_api_key(user_id, api_key)
    await message.answer(
        "✅ API ключ успешно сохранен!\n\n"
        "Теперь вам доступны все функции бота.",
        reply_markup=get_main_menu(True)
    )
    await state.clear()


# Обработчик отмены
@router.message(F.text == "❌ Отмена")
async def cancel_action(message: Message, state: FSMContext):
    """Отмена текущего действия"""
    user_id = message.from_user.id
    has_subscription = await db.has_active_subscription(user_id)

    await state.clear()
    await message.answer(
        "❌ Действие отменено",
        reply_markup=get_main_menu(has_subscription)
    )


# Обработчик показа текущего ключа
@router.callback_query(F.data == "show_api_key")
async def show_api_key(callback: CallbackQuery):
    """Показ текущего API ключа"""
    user_id = callback.from_user.id
    api_key = await db.get_wb_api_key(user_id)

    if api_key:
        # Маскируем ключ
        masked_key = api_key[:10] + "*" * (len(api_key) - 20) + api_key[-10:]
        await callback.message.answer(f"🔑 Ваш текущий API ключ:\n\n<code>{masked_key}</code>", parse_mode="HTML")
    else:
        await callback.message.answer("⚠️ API ключ не установлен")

    await callback.answer()


# Обработчик удаления ключа
@router.callback_query(F.data == "delete_api_key")
async def delete_api_key(callback: CallbackQuery):
    """Удаление API ключа"""
    user_id = callback.from_user.id
    await db.set_wb_api_key(user_id, "")
    await callback.message.answer(
        "🗑️ API ключ удален",
        reply_markup=get_main_menu(False)
    )
    await callback.answer()


# Обработчик возврата в главное меню
@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    user_id = callback.from_user.id
    has_subscription = await db.has_active_subscription(user_id)

    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except:
        pass

    await callback.answer("✅ Возврат в главное меню")


# Обработчик переключения дефолтных ключей
@router.callback_query(F.data == "toggle_default_keys")
async def toggle_default_keys_handler(callback: CallbackQuery):
    """Переключение использования системных (дефолтных) ключей"""
    user_id = callback.from_user.id

    # Проверка активной подписки
    if not await db.has_active_subscription(user_id):
        await callback.answer("⚠️ Необходима активная подписка", show_alert=True)
        return

    # Переключаем настройку
    new_state = await db.toggle_default_keys(user_id)

    status_text = "включены ✅" if new_state else "выключены ❌"

    await callback.message.edit_text(
        f"⚙️ Настройки бота\n\nСистемные ключи теперь {status_text}",
        reply_markup=get_settings_menu(new_state)
    )
    await callback.answer(f"Системные ключи {status_text}")


# Обработчик загрузки Excel файла
@router.callback_query(F.data == "upload_excel")
async def upload_excel_start(callback: CallbackQuery, state: FSMContext):
    """Начало процесса загрузки Excel файла"""
    user_id = callback.from_user.id

    # Проверка активной подписки
    if not await db.has_active_subscription(user_id):
        await callback.answer("⚠️ Необходима активная подписка", show_alert=True)
        return

    await callback.message.answer(
        "📊 Отправьте Excel файл (.xlsx или .xls)\n\n"
        "Этот файл будет использоваться для работы с товарами.\n"
        "Вы можете обновить файл в любой момент.",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(UploadExcel.waiting_for_file)
    await callback.answer()


# Обработчик получения Excel файла
@router.message(UploadExcel.waiting_for_file, F.document)
async def upload_excel_process(message: Message, state: FSMContext):
    """Сохранение Excel файла"""
    user_id = message.from_user.id
    document = message.document

    logger.info(f"Получен файл от пользователя {user_id}: {document.file_name}")

    # Проверяем расширение файла
    if not document.file_name.endswith(('.xlsx', '.xls')):
        logger.warning(f"Неверное расширение файла: {document.file_name}")
        await message.answer("❌ Пожалуйста, отправьте файл Excel (.xlsx или .xls)")
        return

    try:
        # Создаем папку для файлов если её нет
        files_dir = "user_files"
        os.makedirs(files_dir, exist_ok=True)
        logger.info(f"Директория {files_dir} создана/проверена")

        # Формируем путь к файлу
        file_path = os.path.join(files_dir, f"{user_id}_{document.file_name}")
        logger.info(f"Путь к файлу: {file_path}")

        # Скачиваем файл
        await bot.download(document, destination=file_path)
        logger.info(f"Файл скачан: {file_path}")

        # Сохраняем информацию в БД
        await db.set_excel_file(user_id, file_path, document.file_name)
        logger.info(f"Информация о файле сохранена в БД для пользователя {user_id}")

        await message.answer(
            f"✅ Excel файл '{document.file_name}' успешно загружен!\n\n"
            "Файл будет использоваться для работы с товарами.",
            reply_markup=get_main_menu(True)  # Пользователь с подпиской
        )
        await state.clear()
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла: {e}")
        await message.answer(f"❌ Ошибка при загрузке файла: {str(e)}")
        await state.clear()


# Обработчик показа текущего файла
@router.callback_query(F.data == "show_excel_file")
async def show_excel_file(callback: CallbackQuery):
    """Показ информации о текущем Excel файле"""
    user_id = callback.from_user.id

    # Проверка активной подписки
    if not await db.has_active_subscription(user_id):
        await callback.answer("⚠️ Необходима активная подписка", show_alert=True)
        return

    logger.info(f"show_excel_file вызван для user_id={user_id}")
    file_data = await db.get_excel_file(user_id)
    logger.info(f"Полученные данные файла: {file_data}")

    if file_data:
        file_path, file_name = file_data
        # Проверяем существование файла
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path) / 1024  # в KB
            await callback.message.answer(
                f"📊 Текущий Excel файл:\n\n"
                f"Имя: {file_name}\n"
                f"Размер: {file_size:.1f} KB"
            )
        else:
            await callback.message.answer(
                "⚠️ Файл был удален с сервера. Загрузите новый файл."
            )
    else:
        await callback.message.answer("⚠️ Excel файл не загружен")

    await callback.answer()


# Обработчик удаления Excel файла
@router.callback_query(F.data == "delete_excel_file")
async def delete_excel_file(callback: CallbackQuery):
    """Удаление Excel файла"""
    user_id = callback.from_user.id

    # Проверка активной подписки
    if not await db.has_active_subscription(user_id):
        await callback.answer("⚠️ Необходима активная подписка", show_alert=True)
        return

    file_data = await db.get_excel_file(user_id)

    if file_data:
        file_path, file_name = file_data
        # Удаляем файл с диска если он существует
        if os.path.exists(file_path):
            os.remove(file_path)

        # Удаляем информацию из БД
        await db.delete_excel_file(user_id)

        await callback.message.answer(
            f"🗑️ Excel файл '{file_name}' удален",
            reply_markup=get_main_menu(True)  # Пользователь с подпиской
        )
    else:
        await callback.message.answer("⚠️ Excel файл не найден")

    await callback.answer()


# ============ Обработчик настройки порога скидки ============

@router.callback_query(F.data == "set_threshold")
async def set_threshold_start(callback: CallbackQuery, state: FSMContext):
    """Начало процесса настройки порога скидки"""
    user_id = callback.from_user.id

    # Проверка активной подписки
    if not await db.has_active_subscription(user_id):
        await callback.answer("⚠️ Необходима активная подписка", show_alert=True)
        return

    current_threshold = await db.get_discount_threshold(user_id)

    await callback.message.answer(
        f"📈 Настройка порога скидки\n\n"
        f"Текущий порог: {current_threshold}%\n\n"
        f"Отправьте новое значение порога (от 0 до 100).\n"
        f"Будут показаны товары с реальной скидкой >= этого значения.",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(SetThreshold.waiting_for_threshold)
    await callback.answer()


@router.message(SetThreshold.waiting_for_threshold)
async def set_threshold_process(message: Message, state: FSMContext):
    """Обработка нового значения порога"""
    if message.text == "❌ Отмена":
        await state.clear()
        has_subscription = await db.has_active_subscription(message.from_user.id)
        await message.answer(
            "Настройка порога отменена",
            reply_markup=get_main_menu(has_subscription)
        )
        return

    try:
        threshold = int(message.text)
        if threshold < 0 or threshold > 100:
            await message.answer(
                "❌ Пожалуйста, введите число от 0 до 100"
            )
            return

        user_id = message.from_user.id
        await db.set_discount_threshold(user_id, threshold)
        await state.clear()

        await message.answer(
            f"✅ Порог скидки установлен: {threshold}%\n\n"
            f"Теперь при поиске товаров будут показаны только те, "
            f"у которых реальная скидка >= {threshold}%",
            reply_markup=get_main_menu(True)  # Пользователь с подпиской
        )
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите целое число от 0 до 100"
        )


# ============ Обработчики управления API ключами ============

@router.callback_query(F.data == "manage_api_keys")
async def manage_api_keys(callback: CallbackQuery):
    """Меню управления API ключами"""
    user_id = callback.from_user.id

    # Проверка активной подписки
    if not await db.has_active_subscription(user_id):
        await callback.answer("⚠️ Необходима активная подписка", show_alert=True)
        return

    await callback.message.edit_text(
        "🔑 Управление API ключами\n\n"
        "Здесь вы можете добавлять несколько API ключей "
        "и управлять ими (включать/выключать, редактировать, удалять).",
        reply_markup=get_api_keys_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_settings")
async def back_to_settings(callback: CallbackQuery):
    """Возврат в настройки"""
    user_id = callback.from_user.id

    # Проверка активной подписки
    if not await db.has_active_subscription(user_id):
        await callback.answer("⚠️ Необходима активная подписка", show_alert=True)
        return

    use_default_keys = await db.get_use_default_keys(user_id)

    await callback.message.edit_text(
        "⚙️ Настройки бота\n\n"
        "Выберите раздел для настройки:",
        reply_markup=get_settings_menu(use_default_keys)
    )
    await callback.answer()


@router.callback_query(F.data == "list_api_keys")
async def list_api_keys(callback: CallbackQuery):
    """Список всех API ключей пользователя"""
    user_id = callback.from_user.id

    # Проверка активной подписки
    if not await db.has_active_subscription(user_id):
        await callback.answer("⚠️ Необходима активная подписка", show_alert=True)
        return

    keys = await db.get_all_api_keys(user_id)

    if not keys:
        await callback.message.edit_text(
            "📋 У вас пока нет сохраненных API ключей\n\n"
            "Добавьте первый ключ, чтобы начать работу.",
            reply_markup=get_api_keys_menu()
        )
    else:
        await callback.message.edit_text(
            f"📋 Ваши API ключи ({len(keys)}):\n\n"
            "✅ - активный\n"
            "❌ - выключен\n\n"
            "Нажмите на ключ для управления",
            reply_markup=get_api_keys_list_keyboard(keys)
        )

    await callback.answer()


@router.callback_query(F.data.startswith("view_key:"))
async def view_key(callback: CallbackQuery):
    """Просмотр конкретного ключа"""
    user_id = callback.from_user.id

    # Проверка активной подписки
    if not await db.has_active_subscription(user_id):
        await callback.answer("⚠️ Необходима активная подписка", show_alert=True)
        return

    key_id = int(callback.data.split(":")[1])
    key_data = await db.get_api_key_by_id(key_id)

    if not key_data:
        await callback.answer("❌ Ключ не найден", show_alert=True)
        return

    # Маскируем ключ
    masked_key = key_data['key'][:10] + "*" * (len(key_data['key']) - 20) + key_data['key'][-10:]
    status = "✅ Активен" if key_data['is_active'] else "❌ Выключен"

    await callback.message.edit_text(
        f"🔑 API Ключ\n\n"
        f"Название: {key_data['name']}\n"
        f"Статус: {status}\n"
        f"Ключ: <code>{masked_key}</code>\n\n"
        f"Выберите действие:",
        parse_mode="HTML",
        reply_markup=get_key_actions_keyboard(key_id, key_data['is_active'])
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_key:"))
async def toggle_key(callback: CallbackQuery):
    """Включение/выключение ключа"""
    user_id = callback.from_user.id

    # Проверка активной подписки
    if not await db.has_active_subscription(user_id):
        await callback.answer("⚠️ Необходима активная подписка", show_alert=True)
        return

    key_id = int(callback.data.split(":")[1])

    await db.toggle_api_key(key_id)

    # Обновляем сообщение
    key_data = await db.get_api_key_by_id(key_id)
    masked_key = key_data['key'][:10] + "*" * (len(key_data['key']) - 20) + key_data['key'][-10:]
    status = "✅ Активен" if key_data['is_active'] else "❌ Выключен"

    await callback.message.edit_text(
        f"🔑 API Ключ\n\n"
        f"Название: {key_data['name']}\n"
        f"Статус: {status}\n"
        f"Ключ: <code>{masked_key}</code>\n\n"
        f"Выберите действие:",
        parse_mode="HTML",
        reply_markup=get_key_actions_keyboard(key_id, key_data['is_active'])
    )

    status_text = "включен" if key_data['is_active'] else "выключен"
    await callback.answer(f"✅ Ключ {status_text}")


@router.callback_query(F.data.startswith("delete_key:"))
async def delete_key_confirm(callback: CallbackQuery):
    """Подтверждение удаления ключа"""
    user_id = callback.from_user.id

    # Проверка активной подписки
    if not await db.has_active_subscription(user_id):
        await callback.answer("⚠️ Необходима активная подписка", show_alert=True)
        return

    key_id = int(callback.data.split(":")[1])
    key_data = await db.get_api_key_by_id(key_id)

    if not key_data:
        await callback.answer("❌ Ключ не найден", show_alert=True)
        return

    await callback.message.edit_text(
        f"⚠️ Удаление ключа\n\n"
        f"Вы уверены, что хотите удалить ключ '{key_data['name']}'?\n\n"
        f"Это действие нельзя отменить.",
        reply_markup=get_confirm_delete_keyboard(key_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_key:"))
async def delete_key_confirmed(callback: CallbackQuery):
    """Удаление ключа после подтверждения"""
    user_id = callback.from_user.id

    # Проверка активной подписки
    if not await db.has_active_subscription(user_id):
        await callback.answer("⚠️ Необходима активная подписка", show_alert=True)
        return

    key_id = int(callback.data.split(":")[1])
    key_data = await db.get_api_key_by_id(key_id)

    if key_data:
        await db.delete_api_key(key_id)
        await callback.answer(f"✅ Ключ '{key_data['name']}' удален")

        # Показываем обновленный список
        user_id = callback.from_user.id
        keys = await db.get_all_api_keys(user_id)

        if not keys:
            await callback.message.edit_text(
                "📋 У вас больше нет сохраненных API ключей\n\n"
                "Добавьте новый ключ, чтобы продолжить работу.",
                reply_markup=get_api_keys_menu()
            )
        else:
            await callback.message.edit_text(
                f"📋 Ваши API ключи ({len(keys)}):\n\n"
                "✅ - активный\n"
                "❌ - выключен\n\n"
                "Нажмите на ключ для управления",
                reply_markup=get_api_keys_list_keyboard(keys)
            )
    else:
        await callback.answer("❌ Ключ не найден", show_alert=True)


@router.callback_query(F.data == "add_new_api_key")
async def add_new_api_key_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления нового ключа"""
    user_id = callback.from_user.id

    # Проверка активной подписки
    if not await db.has_active_subscription(user_id):
        await callback.answer("⚠️ Необходима активная подписка", show_alert=True)
        return

    await callback.message.answer(
        "➕ Добавление нового API ключа\n\n"
        "Шаг 1/2: Введите название для ключа\n\n"
        "Например: 'Основной', 'Тестовый', 'Магазин 1' и т.д.",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AddApiKey.waiting_for_name)
    await callback.answer()


@router.message(AddApiKey.waiting_for_name, F.text != "❌ Отмена")
async def add_api_key_name(message: Message, state: FSMContext):
    """Получение названия ключа"""
    key_name = message.text.strip()

    if len(key_name) < 2:
        await message.answer("❌ Название слишком короткое. Введите минимум 2 символа.")
        return

    # Сохраняем название в состояние
    await state.update_data(key_name=key_name)

    await message.answer(
        f"✅ Название: {key_name}\n\n"
        "Шаг 2/2: Отправьте ваш WB API ключ\n\n"
        "Получить ключ можно в личном кабинете Wildberries:\n"
        "Настройки → Доступ к API → Создать новый токен\n\n"
        "⚠️ Внимание: ключ должен иметь права на:\n"
        "• Цены и скидки - Просмотр",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AddApiKey.waiting_for_key)


@router.message(AddApiKey.waiting_for_key, F.text != "❌ Отмена")
async def add_api_key_value(message: Message, state: FSMContext):
    """Получение значения ключа"""
    api_key = message.text.strip()
    user_id = message.from_user.id

    # Простая валидация
    if len(api_key) < 20:
        await message.answer("❌ Ключ слишком короткий. Проверьте правильность ввода.")
        return

    # Получаем название из состояния
    data = await state.get_data()
    key_name = data.get('key_name')

    # Сохраняем ключ в БД
    await db.add_api_key(user_id, key_name, api_key)

    await message.answer(
        f"✅ API ключ '{key_name}' успешно добавлен!\n\n"
        "Ключ автоматически активирован и будет использоваться при запросах.",
        reply_markup=get_main_menu(True)
    )
    await state.clear()


@router.callback_query(F.data.startswith("edit_key_name:"))
async def edit_key_name_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования названия ключа"""
    user_id = callback.from_user.id

    # Проверка активной подписки
    if not await db.has_active_subscription(user_id):
        await callback.answer("⚠️ Необходима активная подписка", show_alert=True)
        return

    key_id = int(callback.data.split(":")[1])
    key_data = await db.get_api_key_by_id(key_id)

    if not key_data:
        await callback.answer("❌ Ключ не найден", show_alert=True)
        return

    await state.update_data(key_id=key_id)

    await callback.message.answer(
        f"✏️ Редактирование названия ключа\n\n"
        f"Текущее название: {key_data['name']}\n\n"
        f"Введите новое название:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(EditApiKeyName.waiting_for_name)
    await callback.answer()


@router.message(EditApiKeyName.waiting_for_name, F.text != "❌ Отмена")
async def edit_key_name_process(message: Message, state: FSMContext):
    """Обработка нового названия ключа"""
    new_name = message.text.strip()

    if len(new_name) < 2:
        await message.answer("❌ Название слишком короткое. Введите минимум 2 символа.")
        return

    data = await state.get_data()
    key_id = data.get('key_id')

    await db.update_api_key(key_id, key_name=new_name)

    await message.answer(
        f"✅ Название ключа обновлено на '{new_name}'",
        reply_markup=get_main_menu(True)
    )
    await state.clear()


@router.callback_query(F.data.startswith("edit_key_value:"))
async def edit_key_value_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования значения ключа"""
    user_id = callback.from_user.id

    # Проверка активной подписки
    if not await db.has_active_subscription(user_id):
        await callback.answer("⚠️ Необходима активная подписка", show_alert=True)
        return

    key_id = int(callback.data.split(":")[1])
    key_data = await db.get_api_key_by_id(key_id)

    if not key_data:
        await callback.answer("❌ Ключ не найден", show_alert=True)
        return

    await state.update_data(key_id=key_id)

    await callback.message.answer(
        f"🔄 Редактирование API ключа\n\n"
        f"Ключ: {key_data['name']}\n\n"
        f"Введите новое значение API ключа:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(EditApiKeyValue.waiting_for_key)
    await callback.answer()


@router.message(EditApiKeyValue.waiting_for_key, F.text != "❌ Отмена")
async def edit_key_value_process(message: Message, state: FSMContext):
    """Обработка нового значения ключа"""
    new_key = message.text.strip()

    # Простая валидация
    if len(new_key) < 20:
        await message.answer("❌ Ключ слишком короткий. Проверьте правильность ввода.")
        return

    data = await state.get_data()
    key_id = data.get('key_id')

    await db.update_api_key(key_id, api_key=new_key)

    await message.answer(
        f"✅ Значение API ключа обновлено",
        reply_markup=get_main_menu(True)
    )
    await state.clear()


# ============ Обработчики подписки ============

@router.message(F.text == "💳 Подписка")
async def subscription_status(message: Message):
    """Показ статуса подписки"""
    user_id = message.from_user.id
    subscription = await db.get_active_subscription(user_id)

    # Проверяем наличие привязанных карт
    payment_methods = await db.get_user_payment_methods(user_id)
    has_cards = len(payment_methods) > 0

    if subscription:
        from datetime import datetime
        end_date = datetime.fromisoformat(subscription['end_date'])
        days_left = (end_date - datetime.now()).days

        plan = SUBSCRIPTION_PLANS.get(subscription['plan_id'], {})
        plan_name = plan.get('name', 'Неизвестный план')

        await message.answer(
            f"💳 Ваша подписка\n\n"
            f"Тариф: {plan_name}\n"
            f"Действует до: {end_date.strftime('%d.%m.%Y')}\n"
            f"Осталось дней: {days_left}\n\n"
            f"После окончания подписки доступ к функциям бота будет ограничен.",
            reply_markup=get_subscription_with_cards_keyboard(True, has_cards)
        )
    else:
        await message.answer(
            "💳 Подписка\n\n"
            "У вас нет активной подписки.\n\n"
            "Оформите подписку для получения полного доступа ко всем функциям бота:\n"
            "• Неограниченный поиск товаров\n"
            "• Работа со всеми API ключами\n"
            "• Приоритетная поддержка",
            reply_markup=get_subscription_with_cards_keyboard(False, has_cards)
        )


@router.callback_query(F.data == "show_subscription_plans")
async def show_subscription_plans(callback: CallbackQuery):
    """Показ доступных тарифов"""
    await callback.message.edit_text(
        "💳 Оформление подписки\n\n"
        "Подписка включает:\n"
        "✅ Неограниченный поиск товаров\n"
        "✅ Работа со всеми API ключами\n"
        "✅ Загрузка Excel файлов\n"
        "✅ Настройка порогов скидок\n\n"
        "Выберите тариф:",
        reply_markup=get_subscription_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "renew_subscription")
async def renew_subscription(callback: CallbackQuery):
    """Продление подписки"""
    await callback.message.edit_text(
        "📝 Продление подписки\n\n"
        "Продлите подписку для сохранения доступа ко всем функциям:\n"
        "✅ Неограниченный поиск товаров\n"
        "✅ Работа со всеми API ключами\n"
        "✅ Загрузка Excel файлов\n"
        "✅ Настройка порогов скидок",
        reply_markup=get_subscription_menu()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("subscribe:"))
async def process_subscription(callback: CallbackQuery):
    """Обработка выбора тарифа и создание платежа ЮKassa"""
    user_id = callback.from_user.id
    plan_id = callback.data.split(":")[1]

    plan = SUBSCRIPTION_PLANS.get(plan_id)
    if not plan:
        await callback.answer("❌ Неверный тариф", show_alert=True)
        return

    # Создаем платеж через ЮKassa
    payment_data = YuKassaPayment.create_payment(
        amount=plan['price'],
        description=plan['description'],
        user_id=user_id,
        return_url=f"https://t.me/{(await bot.me()).username}",
        save_payment_method=True  # Сохраняем платежный метод для автоплатежей
    )

    if payment_data:
        # Сохраняем информацию о платеже в БД
        await db.create_payment(
            user_id=user_id,
            payment_id=payment_data['id'],
            plan_id=plan_id,
            amount=plan['price'],
            description=plan['description'],
            confirmation_url=payment_data['confirmation_url'],
            test=payment_data['test']
        )

        payment_url = payment_data['confirmation_url']

        # Создаем inline кнопки
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        check_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить", url=payment_url)],
            [InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f"check_payment:{payment_data['id']}")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="back_to_menu")]
        ])

        test_mode_text = "\n\n⚠️ <b>ТЕСТОВЫЙ РЕЖИМ</b>\nИспользуйте тестовую карту: 5555 5555 5555 4477" if payment_data['test'] else ""

        await callback.message.edit_text(
            f"💳 Оформление подписки\n\n"
            f"Тариф: {plan['name']}\n"
            f"Стоимость: {plan['price']} ₽\n"
            f"Срок: {plan['duration_days']} дней\n\n"
            f"1️⃣ Нажмите кнопку 'Оплатить' для перехода к оплате\n"
            f"2️⃣ После оплаты вернитесь в бот и нажмите 'Проверить оплату'"
            f"{test_mode_text}",
            reply_markup=check_keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
    else:
        logger.error(f"Ошибка создания платежа для пользователя {user_id}")

        await callback.message.edit_text(
            f"❌ Ошибка при создании платежа\n\n"
            f"Попробуйте позже или обратитесь в поддержку."
        )
        await callback.answer("Ошибка создания платежа", show_alert=True)


# ============ Обработчик проверки оплаты ============

@router.callback_query(F.data.startswith("check_payment:"))
async def check_payment_status(callback: CallbackQuery):
    """Проверка статуса платежа по запросу пользователя"""
    payment_id = callback.data.split(":")[1]
    user_id = callback.from_user.id

    await callback.answer("⏳ Проверяю статус оплаты...")

    # Получаем информацию о платеже через API ЮKassa
    payment_info = YuKassaPayment.get_payment(payment_id)

    if not payment_info:
        await callback.message.edit_text(
            "❌ Ошибка проверки платежа\n\n"
            "Не удалось получить информацию о платеже.\n"
            "Попробуйте позже или обратитесь в поддержку."
        )
        return

    status = payment_info['status']
    paid = payment_info['paid']

    # Обновляем статус платежа в БД
    await db.update_payment_status(payment_id, status, paid)

    if status == 'succeeded' and paid:
        # Платеж успешен - сохраняем платежный метод и активируем подписку

        # Сохраняем платежный метод, если он был использован
        if 'payment_method' in payment_info and payment_info['payment_method'].get('saved'):
            payment_method = payment_info['payment_method']
            card_data = payment_method.get('card') if payment_method['type'] == 'bank_card' else None

            await db.save_payment_method(
                user_id=user_id,
                payment_method_id=payment_method['id'],
                payment_method_type=payment_method['type'],
                card_data=card_data
            )
            logger.info(f"Сохранен платежный метод {payment_method['id']} для пользователя {user_id}")

        # Активируем подписку
        success = await db.activate_subscription_yukassa(payment_id)

        if success:
            subscription = await db.get_active_subscription(user_id)
            from datetime import datetime
            end_date = datetime.fromisoformat(subscription['end_date'])

            # Удаляем inline сообщение
            await callback.message.delete()

            # Отправляем новое сообщение с результатом
            await callback.message.answer(
                f"✅ <b>Оплата прошла успешно!</b>\n\n"
                f"Подписка активирована до: {end_date.strftime('%d.%m.%Y')}\n\n"
                f"Спасибо за покупку! Теперь вам доступны все функции бота. 🎉",
                reply_markup=get_main_menu(True),
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                "❌ Ошибка активации подписки\n\n"
                "Платеж прошел, но возникла ошибка активации. "
                "Обратитесь в поддержку."
            )

    elif status == 'pending' or status == 'waiting_for_capture':
        # Платеж еще обрабатывается
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        check_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f"check_payment:{payment_id}")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="back_to_menu")]
        ])

        await callback.message.edit_text(
            f"⏳ Платеж в обработке\n\n"
            f"Ваш платеж еще обрабатывается платежной системой.\n"
            f"Обычно это занимает несколько минут.\n\n"
            f"Попробуйте проверить статус через минуту.",
            reply_markup=check_keyboard
        )

    elif status == 'canceled':
        # Платеж отменен
        payment_methods = await db.get_user_payment_methods(user_id)
        has_cards = len(payment_methods) > 0

        await callback.message.edit_text(
            f"❌ Платеж отменен\n\n"
            f"Платеж был отменен.\n"
            f"Если это произошло по ошибке, попробуйте оформить подписку снова.",
            reply_markup=get_subscription_with_cards_keyboard(False, has_cards)
        )

    else:
        # Неизвестный статус
        await callback.message.edit_text(
            f"❓ Неизвестный статус: {status}\n\n"
            f"Обратитесь в поддержку для уточнения."
        )


# ============ Обработчики управления картами ============

@router.callback_query(F.data == "subscription_info")
async def subscription_info_callback(callback: CallbackQuery):
    """Возврат к информации о подписке"""
    await subscription_status(callback.message)
    await callback.answer()


@router.callback_query(F.data == "manage_cards")
async def manage_cards(callback: CallbackQuery):
    """Показ списка привязанных карт"""
    user_id = callback.from_user.id
    payment_methods = await db.get_user_payment_methods(user_id)

    if not payment_methods:
        await callback.message.edit_text(
            "💳 Управление картами\n\n"
            "У вас нет привязанных карт.\n\n"
            "Карты автоматически сохраняются при первой оплате подписки.",
            reply_markup=get_subscription_with_cards_keyboard(
                await db.has_active_subscription(user_id),
                False
            )
        )
        await callback.answer()
        return

    cards_text = "💳 Ваши привязанные карты:\n\n"
    for method in payment_methods:
        if method['type'] == 'bank_card':
            card_info = f"•••• {method['card_last4']}"
            if method['card_type']:
                card_info += f" ({method['card_type']})"
            cards_text += f"• {card_info}\n"

    cards_text += "\nВыберите карту для управления:"

    await callback.message.edit_text(
        cards_text,
        reply_markup=get_payment_methods_keyboard(payment_methods)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("view_card:"))
async def view_card(callback: CallbackQuery):
    """Просмотр информации о карте"""
    payment_method_id = callback.data.split(":")[1]
    method = await db.get_payment_method_by_id(payment_method_id)

    if not method:
        await callback.answer("❌ Карта не найдена", show_alert=True)
        return

    card_text = "💳 Информация о карте\n\n"

    if method['type'] == 'bank_card':
        card_text += f"Номер: •••• {method['card_last4']}\n"
        if method['card_type']:
            card_text += f"Тип: {method['card_type']}\n"
        if method['card_expiry_month'] and method['card_expiry_year']:
            card_text += f"Срок: {method['card_expiry_month']}/{method['card_expiry_year']}\n"

    await callback.message.edit_text(
        card_text,
        reply_markup=get_card_actions_keyboard(payment_method_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("unbind_card:"))
async def unbind_card(callback: CallbackQuery):
    """Запрос подтверждения отвязки карты"""
    payment_method_id = callback.data.split(":")[1]

    await callback.message.edit_text(
        "⚠️ Подтвердите отвязку карты\n\n"
        "Вы уверены, что хотите отвязать эту карту?\n"
        "Для следующих платежей потребуется повторно вводить данные карты.",
        reply_markup=get_confirm_unbind_card_keyboard(payment_method_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_unbind_card:"))
async def confirm_unbind_card(callback: CallbackQuery):
    """Подтверждение отвязки карты"""
    payment_method_id = callback.data.split(":")[1]

    await db.delete_payment_method(payment_method_id)

    await callback.answer("✅ Карта успешно отвязана", show_alert=True)

    # Возвращаемся к списку карт
    await manage_cards(callback)


async def main():
    """Главная функция запуска бота"""
    # Создаем таблицы в БД
    await db.create_tables()

    # Регистрируем роутер
    dp.include_router(router)

    # Запускаем бота
    logger.info("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
