"""Модуль для работы с базой данных"""
import aiosqlite
from config import DB_NAME
from crypto_helper import CryptoHelper


class Database:
    def __init__(self, db_name: str = DB_NAME):
        self.db_name = db_name
        self.crypto = CryptoHelper()

    async def create_tables(self):
        """Создание таблиц в базе данных"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    wb_api_key TEXT,
                    excel_file_path TEXT,
                    excel_file_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Таблица для хранения нескольких API ключей
            await db.execute('''
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    key_name TEXT,
                    api_key TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')

            # Таблица для хранения подписок
            await db.execute('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    plan_id TEXT,
                    yandex_order_id TEXT UNIQUE,
                    status TEXT DEFAULT 'pending',
                    amount TEXT,
                    start_date TIMESTAMP,
                    end_date TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')

            # Таблица для хранения платежей ЮKassa
            await db.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    payment_id TEXT UNIQUE,
                    plan_id TEXT,
                    amount TEXT,
                    currency TEXT DEFAULT 'RUB',
                    status TEXT DEFAULT 'pending',
                    paid BOOLEAN DEFAULT 0,
                    test BOOLEAN DEFAULT 0,
                    description TEXT,
                    confirmation_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')

            # Таблица для хранения привязанных платежных методов (карт)
            await db.execute('''
                CREATE TABLE IF NOT EXISTS payment_methods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    payment_method_id TEXT UNIQUE,
                    payment_method_type TEXT,
                    card_last4 TEXT,
                    card_first6 TEXT,
                    card_type TEXT,
                    card_expiry_month TEXT,
                    card_expiry_year TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')

            # Миграция: добавляем новые столбцы если их нет
            try:
                # Проверяем наличие столбца excel_file_path
                cursor = await db.execute("PRAGMA table_info(users)")
                columns = await cursor.fetchall()
                column_names = [col[1] for col in columns]

                if 'excel_file_path' not in column_names:
                    await db.execute('ALTER TABLE users ADD COLUMN excel_file_path TEXT')

                if 'excel_file_name' not in column_names:
                    await db.execute('ALTER TABLE users ADD COLUMN excel_file_name TEXT')

                if 'discount_threshold' not in column_names:
                    await db.execute('ALTER TABLE users ADD COLUMN discount_threshold INTEGER DEFAULT 28')

                if 'use_default_keys' not in column_names:
                    await db.execute('ALTER TABLE users ADD COLUMN use_default_keys BOOLEAN DEFAULT 1')

                if 'email' not in column_names:
                    await db.execute('ALTER TABLE users ADD COLUMN email TEXT')

            except Exception as e:
                # Если таблица не существует, она будет создана выше
                pass

            await db.commit()

    async def add_user(self, user_id: int, username: str = None):
        """Добавление нового пользователя"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                'INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
                (user_id, username)
            )
            await db.commit()

    async def set_wb_api_key(self, user_id: int, api_key: str):
        """Сохранение WB API ключа пользователя"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                'UPDATE users SET wb_api_key = ? WHERE user_id = ?',
                (api_key, user_id)
            )
            await db.commit()

    async def get_wb_api_key(self, user_id: int) -> str | None:
        """Получение WB API ключа пользователя"""
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                'SELECT wb_api_key FROM users WHERE user_id = ?',
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    async def has_api_key(self, user_id: int) -> bool:
        """Проверка наличия API ключа у пользователя"""
        api_key = await self.get_wb_api_key(user_id)
        return api_key is not None and api_key != ''

    async def set_excel_file(self, user_id: int, file_path: str, file_name: str):
        """Сохранение пути к Excel файлу пользователя"""
        import logging
        logger = logging.getLogger(__name__)

        async with aiosqlite.connect(self.db_name) as db:
            # Сначала проверим существует ли пользователь
            async with db.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,)) as cursor:
                user_exists = await cursor.fetchone()
                logger.info(f"set_excel_file: user {user_id} существует в БД: {user_exists is not None}")

            # Если пользователя нет, создаем его
            if not user_exists:
                logger.info(f"Создаем пользователя {user_id} в таблице users")
                await db.execute(
                    'INSERT INTO users (user_id) VALUES (?)',
                    (user_id,)
                )

            logger.info(f"Обновляем Excel файл для user_id={user_id}: path={file_path}, name={file_name}")
            result = await db.execute(
                'UPDATE users SET excel_file_path = ?, excel_file_name = ? WHERE user_id = ?',
                (file_path, file_name, user_id)
            )
            logger.info(f"UPDATE выполнен, rowcount={result.rowcount}")
            await db.commit()

    async def get_excel_file(self, user_id: int) -> tuple[str, str] | None:
        """Получение пути к Excel файлу пользователя"""
        import logging
        logger = logging.getLogger(__name__)

        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                'SELECT excel_file_path, excel_file_name FROM users WHERE user_id = ?',
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                logger.info(f"get_excel_file для user_id={user_id}: row={row}")
                if row:
                    logger.info(f"excel_file_path={row[0]}, excel_file_name={row[1]}")
                return (row[0], row[1]) if row and row[0] else None

    async def has_excel_file(self, user_id: int) -> bool:
        """Проверка наличия Excel файла у пользователя"""
        file_data = await self.get_excel_file(user_id)
        return file_data is not None

    async def delete_excel_file(self, user_id: int):
        """Удаление информации о Excel файле пользователя"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                'UPDATE users SET excel_file_path = NULL, excel_file_name = NULL WHERE user_id = ?',
                (user_id,)
            )
            await db.commit()

    # Методы для работы с несколькими API ключами
    async def add_api_key(self, user_id: int, key_name: str, api_key: str):
        """Добавление нового API ключа (с шифрованием)"""
        encrypted_key = self.crypto.encrypt(api_key)
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                'INSERT INTO api_keys (user_id, key_name, api_key) VALUES (?, ?, ?)',
                (user_id, key_name, encrypted_key)
            )
            await db.commit()

    async def get_all_api_keys(self, user_id: int):
        """Получение всех API ключей пользователя (с дешифрованием)"""
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                'SELECT id, key_name, api_key, is_active FROM api_keys WHERE user_id = ? ORDER BY id',
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                result = []
                for row in rows:
                    decrypted_key = self.crypto.decrypt(row[2])
                    result.append({
                        'id': row[0],
                        'name': row[1],
                        'key': decrypted_key,
                        'is_active': row[3]
                    })
                return result

    async def get_active_api_keys(self, user_id: int):
        """Получение активных API ключей (с дешифрованием)"""
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                'SELECT id, key_name, api_key FROM api_keys WHERE user_id = ? AND is_active = 1 ORDER BY id',
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                result = []
                for row in rows:
                    decrypted_key = self.crypto.decrypt(row[2])
                    result.append({
                        'id': row[0],
                        'name': row[1],
                        'key': decrypted_key
                    })
                return result

    async def toggle_api_key(self, key_id: int):
        """Включить/выключить API ключ"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                'UPDATE api_keys SET is_active = NOT is_active WHERE id = ?',
                (key_id,)
            )
            await db.commit()

    async def delete_api_key(self, key_id: int):
        """Удаление API ключа"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('DELETE FROM api_keys WHERE id = ?', (key_id,))
            await db.commit()

    async def update_api_key(self, key_id: int, key_name: str = None, api_key: str = None):
        """Обновление API ключа"""
        async with aiosqlite.connect(self.db_name) as db:
            if key_name and api_key:
                encrypted_key = self.crypto.encrypt(api_key)
                await db.execute(
                    'UPDATE api_keys SET key_name = ?, api_key = ? WHERE id = ?',
                    (key_name, encrypted_key, key_id)
                )
            elif key_name:
                await db.execute(
                    'UPDATE api_keys SET key_name = ? WHERE id = ?',
                    (key_name, key_id)
                )
            elif api_key:
                encrypted_key = self.crypto.encrypt(api_key)
                await db.execute(
                    'UPDATE api_keys SET api_key = ? WHERE id = ?',
                    (encrypted_key, key_id)
                )
            await db.commit()

    async def get_api_key_by_id(self, key_id: int):
        """Получение API ключа по ID"""
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                'SELECT id, key_name, api_key, is_active, user_id FROM api_keys WHERE id = ?',
                (key_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    decrypted_key = self.crypto.decrypt(row[2])
                    return {
                        'id': row[0],
                        'name': row[1],
                        'key': decrypted_key,
                        'is_active': row[3],
                        'user_id': row[4]
                    }
                return None

    async def set_discount_threshold(self, user_id: int, threshold: int):
        """Установка порога скидки для пользователя"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                'UPDATE users SET discount_threshold = ? WHERE user_id = ?',
                (threshold, user_id)
            )
            await db.commit()

    async def get_discount_threshold(self, user_id: int) -> int:
        """Получение порога скидки пользователя (по умолчанию 28%)"""
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                'SELECT discount_threshold FROM users WHERE user_id = ?',
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row and row[0] is not None:
                    return row[0]
                return 28  # значение по умолчанию

    async def get_use_default_keys(self, user_id: int) -> bool:
        """Проверка, использует ли пользователь дефолтные ключи (по умолчанию True)"""
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                'SELECT use_default_keys FROM users WHERE user_id = ?',
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row and row[0] is not None:
                    return bool(row[0])
                return True  # по умолчанию включены

    async def toggle_default_keys(self, user_id: int):
        """Переключение использования дефолтных ключей"""
        current = await self.get_use_default_keys(user_id)
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                'UPDATE users SET use_default_keys = ? WHERE user_id = ?',
                (not current, user_id)
            )
            await db.commit()
        return not current

    async def get_active_api_keys_with_defaults(self, user_id: int):
        """Получение активных API ключей пользователя + дефолтные ключи (если включены)"""
        from config import DEFAULT_API_KEYS

        # Получаем ключи пользователя
        user_keys = await self.get_active_api_keys(user_id)

        # Проверяем, нужно ли добавлять дефолтные ключи
        use_defaults = await self.get_use_default_keys(user_id)

        # Добавляем дефолтные ключи (они не видны пользователю)
        all_keys = []

        # Сначала добавляем дефолтные ключи (если включены)
        if use_defaults:
            for idx, default_key in enumerate(DEFAULT_API_KEYS, 1):
                all_keys.append({
                    'id': f'default_{idx}',  # Специальный ID для дефолтных ключей
                    'name': f'Системный ключ {idx}',
                    'key': default_key,
                    'is_default': True  # Флаг что это дефолтный ключ
                })

        # Затем добавляем пользовательские ключи
        for key in user_keys:
            key['is_default'] = False
            all_keys.append(key)

        return all_keys

    # Методы для работы с подписками
    async def create_subscription(self, user_id: int, plan_id: str, yandex_order_id: str, amount: str):
        """Создание новой подписки"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                '''INSERT INTO subscriptions
                   (user_id, plan_id, yandex_order_id, amount, status)
                   VALUES (?, ?, ?, ?, 'pending')''',
                (user_id, plan_id, yandex_order_id, amount)
            )
            await db.commit()

    async def activate_subscription(self, yandex_order_id: str):
        """Активация подписки после успешной оплаты"""
        from datetime import datetime, timedelta
        from config import SUBSCRIPTION_PLANS

        async with aiosqlite.connect(self.db_name) as db:
            # Получаем информацию о новой подписке
            async with db.execute(
                'SELECT user_id, plan_id FROM subscriptions WHERE yandex_order_id = ?',
                (yandex_order_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return False

                user_id = row[0]
                plan_id = row[1]
                plan = SUBSCRIPTION_PLANS.get(plan_id)
                if not plan:
                    return False

                # Проверяем, есть ли активная подписка (исключая текущую)
                async with db.execute(
                    '''SELECT end_date FROM subscriptions
                       WHERE user_id = ? AND status = 'active' AND end_date > ?
                       AND yandex_order_id != ?
                       ORDER BY end_date DESC LIMIT 1''',
                    (user_id, datetime.now(), yandex_order_id)
                ) as active_cursor:
                    active_row = await active_cursor.fetchone()

                    if active_row:
                        # Есть активная подписка - продлеваем от её даты окончания
                        current_end_date = datetime.fromisoformat(active_row[0])
                        start_date = current_end_date
                        end_date = start_date + timedelta(days=plan['duration_days'])

                        # ВАЖНО: Деактивируем старую подписку, чтобы избежать повторных списаний
                        await db.execute(
                            '''UPDATE subscriptions
                               SET status = 'renewed', updated_at = ?
                               WHERE user_id = ? AND status = 'active' AND yandex_order_id != ?''',
                            (datetime.now(), user_id, yandex_order_id)
                        )
                    else:
                        # Нет активной подписки - начинаем с текущего момента
                        start_date = datetime.now()
                        end_date = start_date + timedelta(days=plan['duration_days'])

                # Обновляем подписку
                await db.execute(
                    '''UPDATE subscriptions
                       SET status = 'active', start_date = ?, end_date = ?, updated_at = ?
                       WHERE yandex_order_id = ?''',
                    (start_date, end_date, datetime.now(), yandex_order_id)
                )
                await db.commit()
                return True

    async def get_active_subscription(self, user_id: int):
        """Получение активной подписки пользователя"""
        from datetime import datetime, timedelta
        from config import ADMIN_IDS

        # Администраторы имеют бессрочную подписку
        if user_id in ADMIN_IDS:
            return {
                'id': 0,
                'plan_id': 'admin',
                'start_date': datetime.now().isoformat(),
                'end_date': (datetime.now() + timedelta(days=36500)).isoformat()  # 100 лет
            }

        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                '''SELECT id, plan_id, start_date, end_date
                   FROM subscriptions
                   WHERE user_id = ? AND status = 'active' AND end_date > ?
                   ORDER BY end_date DESC LIMIT 1''',
                (user_id, datetime.now())
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'plan_id': row[1],
                        'start_date': row[2],
                        'end_date': row[3]
                    }
                return None

    async def has_active_subscription(self, user_id: int) -> bool:
        """Проверка наличия активной подписки"""
        subscription = await self.get_active_subscription(user_id)
        return subscription is not None

    async def cancel_subscription(self, yandex_order_id: str):
        """Отмена подписки"""
        from datetime import datetime

        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                '''UPDATE subscriptions
                   SET status = 'cancelled', updated_at = ?
                   WHERE yandex_order_id = ?''',
                (datetime.now(), yandex_order_id)
            )
            await db.commit()

    async def get_subscription_by_order_id(self, yandex_order_id: str):
        """Получение подписки по ID заказа Яндекс Пэй"""
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                '''SELECT id, user_id, plan_id, status, amount, start_date, end_date
                   FROM subscriptions WHERE yandex_order_id = ?''',
                (yandex_order_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'user_id': row[1],
                        'plan_id': row[2],
                        'status': row[3],
                        'amount': row[4],
                        'start_date': row[5],
                        'end_date': row[6]
                    }
                return None

    async def create_trial_subscription(self, user_id: int):
        """Создание пробной подписки на 1 день для нового пользователя"""
        from datetime import datetime, timedelta
        import time

        # Проверяем, есть ли уже подписка (активная или истекшая)
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                'SELECT COUNT(*) FROM subscriptions WHERE user_id = ?',
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row and row[0] > 0:
                    # У пользователя уже была подписка, не даем пробную
                    return False

            # Создаем пробную подписку
            start_date = datetime.now()
            end_date = start_date + timedelta(days=1)
            order_id = f"trial_{user_id}_{int(time.time())}"

            await db.execute(
                '''INSERT INTO subscriptions
                   (user_id, plan_id, yandex_order_id, amount, status, start_date, end_date)
                   VALUES (?, 'trial', ?, '0.00', 'active', ?, ?)''',
                (user_id, order_id, start_date, end_date)
            )
            await db.commit()
            return True

    # Методы для работы с платежами ЮKassa
    async def create_payment(self, user_id: int, payment_id: str, plan_id: str,
                            amount: str, description: str, confirmation_url: str, test: bool = False):
        """Создание записи о платеже"""
        from datetime import datetime

        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                '''INSERT INTO payments
                   (user_id, payment_id, plan_id, amount, description, confirmation_url, test, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (user_id, payment_id, plan_id, amount, description, confirmation_url, test, datetime.now())
            )
            await db.commit()

    async def update_payment_status(self, payment_id: str, status: str, paid: bool):
        """Обновление статуса платежа"""
        from datetime import datetime

        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                '''UPDATE payments
                   SET status = ?, paid = ?, updated_at = ?
                   WHERE payment_id = ?''',
                (status, paid, datetime.now(), payment_id)
            )
            await db.commit()

    async def get_payment_by_id(self, payment_id: str):
        """Получение платежа по ID"""
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                '''SELECT id, user_id, payment_id, plan_id, amount, status, paid, test, description, confirmation_url, created_at
                   FROM payments WHERE payment_id = ?''',
                (payment_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'user_id': row[1],
                        'payment_id': row[2],
                        'plan_id': row[3],
                        'amount': row[4],
                        'status': row[5],
                        'paid': bool(row[6]),
                        'test': bool(row[7]),
                        'description': row[8],
                        'confirmation_url': row[9],
                        'created_at': row[10]
                    }
                return None

    async def get_user_payments(self, user_id: int, limit: int = 10):
        """Получение последних платежей пользователя"""
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                '''SELECT payment_id, plan_id, amount, status, paid, created_at
                   FROM payments
                   WHERE user_id = ?
                   ORDER BY created_at DESC
                   LIMIT ?''',
                (user_id, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [{
                    'payment_id': row[0],
                    'plan_id': row[1],
                    'amount': row[2],
                    'status': row[3],
                    'paid': bool(row[4]),
                    'created_at': row[5]
                } for row in rows]

    async def has_recent_auto_renewal_payment(self, user_id: int, hours: int = 24) -> bool:
        """Проверка, был ли недавно создан платеж автопродления для пользователя"""
        from datetime import datetime, timedelta

        cutoff_time = datetime.now() - timedelta(hours=hours)

        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                '''SELECT COUNT(*) FROM payments
                   WHERE user_id = ?
                     AND description LIKE 'Автопродление:%'
                     AND created_at > ?''',
                (user_id, cutoff_time)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] > 0 if row else False

    # Методы для работы с платежными методами (привязанными картами)
    async def save_payment_method(self, user_id: int, payment_method_id: str, payment_method_type: str,
                                  card_data: dict = None):
        """Сохранение платежного метода"""
        from datetime import datetime

        async with aiosqlite.connect(self.db_name) as db:
            if card_data:
                await db.execute(
                    '''INSERT OR REPLACE INTO payment_methods
                       (user_id, payment_method_id, payment_method_type, card_last4, card_first6,
                        card_type, card_expiry_month, card_expiry_year, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (user_id, payment_method_id, payment_method_type,
                     card_data.get('last4'), card_data.get('first6'), card_data.get('card_type'),
                     card_data.get('expiry_month'), card_data.get('expiry_year'), datetime.now())
                )
            else:
                await db.execute(
                    '''INSERT OR REPLACE INTO payment_methods
                       (user_id, payment_method_id, payment_method_type, created_at)
                       VALUES (?, ?, ?, ?)''',
                    (user_id, payment_method_id, payment_method_type, datetime.now())
                )
            await db.commit()

    async def get_user_payment_methods(self, user_id: int):
        """Получение всех активных платежных методов пользователя"""
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                '''SELECT id, payment_method_id, payment_method_type, card_last4, card_first6,
                          card_type, card_expiry_month, card_expiry_year, created_at
                   FROM payment_methods
                   WHERE user_id = ? AND is_active = 1
                   ORDER BY created_at DESC''',
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [{
                    'id': row[0],
                    'payment_method_id': row[1],
                    'type': row[2],
                    'card_last4': row[3],
                    'card_first6': row[4],
                    'card_type': row[5],
                    'card_expiry_month': row[6],
                    'card_expiry_year': row[7],
                    'created_at': row[8]
                } for row in rows]

    async def delete_payment_method(self, payment_method_id: str):
        """Удаление (деактивация) платежного метода"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                'UPDATE payment_methods SET is_active = 0 WHERE payment_method_id = ?',
                (payment_method_id,)
            )
            await db.commit()

    async def get_payment_method_by_id(self, payment_method_id: str):
        """Получение платежного метода по ID"""
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                '''SELECT id, user_id, payment_method_id, payment_method_type, card_last4, card_first6,
                          card_type, card_expiry_month, card_expiry_year, is_active
                   FROM payment_methods WHERE payment_method_id = ?''',
                (payment_method_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'user_id': row[1],
                        'payment_method_id': row[2],
                        'type': row[3],
                        'card_last4': row[4],
                        'card_first6': row[5],
                        'card_type': row[6],
                        'card_expiry_month': row[7],
                        'card_expiry_year': row[8],
                        'is_active': bool(row[9])
                    }
                return None

    async def has_payment_methods(self, user_id: int) -> bool:
        """Проверка наличия активных платежных методов у пользователя"""
        payment_methods = await self.get_user_payment_methods(user_id)
        return len(payment_methods) > 0

    async def activate_subscription_yukassa(self, payment_id: str):
        """Активация подписки после успешной оплаты через ЮKassa"""
        from datetime import datetime, timedelta
        from config import SUBSCRIPTION_PLANS

        async with aiosqlite.connect(self.db_name) as db:
            # Получаем информацию о платеже
            payment = await self.get_payment_by_id(payment_id)
            if not payment:
                return False

            user_id = payment['user_id']
            plan_id = payment['plan_id']
            plan = SUBSCRIPTION_PLANS.get(plan_id)
            if not plan:
                return False

            # Проверяем, есть ли активная подписка
            async with db.execute(
                '''SELECT end_date FROM subscriptions
                   WHERE user_id = ? AND status = 'active' AND end_date > ?
                   ORDER BY end_date DESC LIMIT 1''',
                (user_id, datetime.now())
            ) as active_cursor:
                active_row = await active_cursor.fetchone()

                if active_row:
                    # Есть активная подписка - продлеваем от её даты окончания
                    current_end_date = datetime.fromisoformat(active_row[0])
                    start_date = current_end_date
                    end_date = start_date + timedelta(days=plan['duration_days'])

                    # ВАЖНО: Деактивируем старую подписку, чтобы избежать повторных списаний
                    await db.execute(
                        '''UPDATE subscriptions
                           SET status = 'renewed', updated_at = ?
                           WHERE user_id = ? AND status = 'active' AND end_date > ?''',
                        (datetime.now(), user_id, datetime.now())
                    )
                else:
                    # Нет активной подписки - начинаем с текущего момента
                    start_date = datetime.now()
                    end_date = start_date + timedelta(days=plan['duration_days'])

            # Создаем новую подписку
            await db.execute(
                '''INSERT INTO subscriptions
                   (user_id, plan_id, yandex_order_id, amount, status, start_date, end_date, created_at)
                   VALUES (?, ?, ?, ?, 'active', ?, ?, ?)''',
                (user_id, plan_id, payment_id, payment['amount'], start_date, end_date, datetime.now())
            )
            await db.commit()
            return True

    async def set_user_email(self, user_id: int, email: str):
        """Сохранение email пользователя"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                'UPDATE users SET email = ? WHERE user_id = ?',
                (email, user_id)
            )
            await db.commit()

    async def get_user_email(self, user_id: int) -> str | None:
        """Получение email пользователя"""
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                'SELECT email FROM users WHERE user_id = ?',
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row and row[0] else None

    async def has_email(self, user_id: int) -> bool:
        """Проверка наличия email у пользователя"""
        email = await self.get_user_email(user_id)
        return email is not None and len(email) > 0

    async def get_expiring_subscriptions(self, days_before: int = 3):
        """Получение подписок, истекающих в ближайшие N дней (только одна на пользователя - самая новая)"""
        from datetime import datetime, timedelta

        # Диапазон дат: от текущего момента до days_before дней вперед
        now = datetime.now()
        future_date = now + timedelta(days=days_before)

        async with aiosqlite.connect(self.db_name) as db:
            # Используем GROUP BY, чтобы получить только одну (самую новую) подписку для каждого пользователя
            async with db.execute(
                '''SELECT user_id, plan_id, end_date
                   FROM subscriptions
                   WHERE status = 'active'
                     AND end_date > ?
                     AND end_date <= ?
                     AND id IN (
                         SELECT MAX(id)
                         FROM subscriptions
                         WHERE status = 'active'
                         GROUP BY user_id
                     )
                   ORDER BY end_date ASC''',
                (now, future_date)
            ) as cursor:
                rows = await cursor.fetchall()
                return [{
                    'user_id': row[0],
                    'plan_id': row[1],
                    'end_date': row[2]
                } for row in rows]
