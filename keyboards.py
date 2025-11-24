"""Клавиатуры для бота"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu(has_api_key: bool = False) -> ReplyKeyboardMarkup:
    """Главное меню бота"""
    keyboard = [
        [KeyboardButton(text="⚙️ Настройки")],
    ]

    if has_api_key:
        keyboard.insert(0, [
            KeyboardButton(text="📦 Список товаров")
        ])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )


def get_settings_menu() -> InlineKeyboardMarkup:
    """Меню настроек"""
    keyboard = [
        [InlineKeyboardButton(text="🔑 Управление API ключами", callback_data="manage_api_keys")],
        [InlineKeyboardButton(text="📊 Загрузить Excel файл", callback_data="upload_excel")],
        [InlineKeyboardButton(text="📋 Показать текущий файл", callback_data="show_excel_file")],
        [InlineKeyboardButton(text="🗑️ Удалить Excel файл", callback_data="delete_excel_file")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
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

    keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="manage_api_keys")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_key_actions_keyboard(key_id: int, is_active: bool) -> InlineKeyboardMarkup:
    """Клавиатура действий с конкретным ключом"""
    toggle_text = "🔴 Выключить" if is_active else "🟢 Включить"

    keyboard = [
        [InlineKeyboardButton(text=toggle_text, callback_data=f"toggle_key:{key_id}")],
        [InlineKeyboardButton(text="✏️ Изменить название", callback_data=f"edit_key_name:{key_id}")],
        [InlineKeyboardButton(text="🔄 Изменить ключ", callback_data=f"edit_key_value:{key_id}")],
        [InlineKeyboardButton(text="🗑️ Удалить ключ", callback_data=f"delete_key:{key_id}")],
        [InlineKeyboardButton(text="◀️ Назад к списку", callback_data="list_api_keys")]
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




def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура отмены"""
    keyboard = [[KeyboardButton(text="❌ Отмена")]]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )
