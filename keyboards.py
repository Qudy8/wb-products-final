"""Клавиатуры для бота"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu(has_subscription: bool = False) -> ReplyKeyboardMarkup:
    """
    Главное меню бота

    Args:
        has_subscription: Наличие активной подписки у пользователя
    """
    if has_subscription:
        # Полное меню для пользователей с подпиской
        keyboard = [
            [KeyboardButton(text="📦 Список товаров")],
            [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="💳 Подписка")],
        ]
        placeholder = "Выберите действие"
    else:
        # Ограниченное меню для пользователей без подписки
        keyboard = [
            [KeyboardButton(text="💳 Подписка")],
        ]
        placeholder = "⚠️ Оформите подписку для доступа к функциям"

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder=placeholder
    )


def get_settings_menu(use_default_keys: bool = True) -> InlineKeyboardMarkup:
    """Меню настроек"""
    default_keys_text = "🔓 Системные ключи: ВКЛ" if use_default_keys else "🔒 Системные ключи: ВЫКЛ"

    keyboard = [
        [InlineKeyboardButton(text="🔑 Управление API ключами", callback_data="manage_api_keys")],
        [InlineKeyboardButton(text=default_keys_text, callback_data="toggle_default_keys")],
        [InlineKeyboardButton(text="📊 Загрузить Excel файл", callback_data="upload_excel")],
        [InlineKeyboardButton(text="📋 Показать текущий файл", callback_data="show_excel_file")],
        [InlineKeyboardButton(text="🗑️ Удалить Excel файл", callback_data="delete_excel_file")],
        [InlineKeyboardButton(text="📈 Настроить порог скидки", callback_data="set_threshold")],
        [InlineKeyboardButton(text="◀️ Закрыть", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_api_keys_menu() -> InlineKeyboardMarkup:
    """Меню управления API ключами"""
    keyboard = [
        [InlineKeyboardButton(text="➕ Добавить новый ключ", callback_data="add_new_api_key")],
        [InlineKeyboardButton(text="📋 Список ключей", callback_data="list_api_keys")],
        [InlineKeyboardButton(text="◀️ Назад к настройкам", callback_data="back_to_settings")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_api_keys_list_keyboard(keys: list) -> InlineKeyboardMarkup:
    """Клавиатура со списком API ключей"""
    keyboard = []

    for key_data in keys:
        key_id = key_data['id']
        key_name = key_data['name']
        is_active = key_data['is_active']

        # Эмодзи статуса
        status_emoji = "✅" if is_active else "❌"

        # Кнопка с названием ключа
        keyboard.append([
            InlineKeyboardButton(
                text=f"{status_emoji} {key_name}",
                callback_data=f"view_key:{key_id}"
            )
        ])

    keyboard.append([InlineKeyboardButton(text="◀️ Управление ключами", callback_data="manage_api_keys")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_key_actions_keyboard(key_id: int, is_active: bool) -> InlineKeyboardMarkup:
    """Клавиатура действий с конкретным ключом"""
    toggle_text = "🔴 Выключить" if is_active else "🟢 Включить"

    keyboard = [
        [InlineKeyboardButton(text=toggle_text, callback_data=f"toggle_key:{key_id}")],
        [InlineKeyboardButton(text="✏️ Изменить название", callback_data=f"edit_key_name:{key_id}")],
        [InlineKeyboardButton(text="🔄 Изменить ключ", callback_data=f"edit_key_value:{key_id}")],
        [InlineKeyboardButton(text="🗑️ Удалить ключ", callback_data=f"delete_key:{key_id}")],
        [InlineKeyboardButton(text="◀️ К списку ключей", callback_data="list_api_keys")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirm_delete_keyboard(key_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления"""
    keyboard = [
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_key:{key_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"view_key:{key_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_pagination_keyboard(current_page: int, total_pages: int, key_name: str = None) -> InlineKeyboardMarkup:
    """
    Клавиатура пагинации для результатов

    Args:
        current_page: текущая страница (от 0)
        total_pages: общее количество страниц
        key_name: название ключа для отображения
    """
    keyboard = []

    # Кнопки навигации
    nav_buttons = []

    if current_page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page:{current_page - 1}"))

    # Показываем номер страницы
    nav_buttons.append(InlineKeyboardButton(text=f"{current_page + 1}/{total_pages}", callback_data="noop"))

    if current_page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"page:{current_page + 1}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)




def get_subscription_menu() -> InlineKeyboardMarkup:
    """Меню выбора тарифа подписки"""
    from config import SUBSCRIPTION_PLANS

    keyboard = []

    for plan_id, plan in SUBSCRIPTION_PLANS.items():
        button_text = f"💳 {plan['name']} - {plan['price']} ₽"
        keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"subscribe:{plan_id}"
            )
        ])

    keyboard.append([InlineKeyboardButton(text="◀️ Закрыть", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_subscription_status_keyboard(has_subscription: bool) -> InlineKeyboardMarkup:
    """Клавиатура статуса подписки"""
    keyboard = []

    if has_subscription:
        keyboard.append([InlineKeyboardButton(text="📝 Продлить подписку", callback_data="renew_subscription")])
    else:
        keyboard.append([InlineKeyboardButton(text="💳 Оформить подписку", callback_data="show_subscription_plans")])

    keyboard.append([InlineKeyboardButton(text="◀️ Закрыть", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура отмены"""
    keyboard = [[KeyboardButton(text="❌ Отмена")]]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )


def get_payment_methods_keyboard(payment_methods: list) -> InlineKeyboardMarkup:
    """Клавиатура со списком привязанных карт"""
    keyboard = []

    for method in payment_methods:
        if method['type'] == 'bank_card' and method['card_last4']:
            card_info = f"💳 •••• {method['card_last4']}"
            if method['card_type']:
                card_info += f" ({method['card_type']})"

            keyboard.append([
                InlineKeyboardButton(
                    text=card_info,
                    callback_data=f"view_card:{method['payment_method_id']}"
                )
            ])

    keyboard.append([InlineKeyboardButton(text="◀️ Назад к подписке", callback_data="subscription_info")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_card_actions_keyboard(payment_method_id: str) -> InlineKeyboardMarkup:
    """Клавиатура действий с картой"""
    keyboard = [
        [InlineKeyboardButton(text="🗑️ Отвязать карту", callback_data=f"unbind_card:{payment_method_id}")],
        [InlineKeyboardButton(text="◀️ К списку карт", callback_data="manage_cards")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirm_unbind_card_keyboard(payment_method_id: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения отвязки карты"""
    keyboard = [
        [InlineKeyboardButton(text="✅ Да, отвязать", callback_data=f"confirm_unbind_card:{payment_method_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"view_card:{payment_method_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_subscription_with_cards_keyboard(has_subscription: bool, has_cards: bool) -> InlineKeyboardMarkup:
    """Расширенная клавиатура статуса подписки с управлением картами"""
    keyboard = []

    if has_subscription:
        keyboard.append([InlineKeyboardButton(text="📝 Продлить подписку", callback_data="renew_subscription")])
    else:
        keyboard.append([InlineKeyboardButton(text="💳 Оформить подписку", callback_data="show_subscription_plans")])

    if has_cards:
        keyboard.append([InlineKeyboardButton(text="💳 Мои карты", callback_data="manage_cards")])

    keyboard.append([InlineKeyboardButton(text="◀️ Закрыть", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
