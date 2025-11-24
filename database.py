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
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                'UPDATE users SET excel_file_path = ?, excel_file_name = ? WHERE user_id = ?',
                (file_path, file_name, user_id)
            )
            await db.commit()

    async def get_excel_file(self, user_id: int) -> tuple[str, str] | None:
        """Получение пути к Excel файлу пользователя"""
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                'SELECT excel_file_path, excel_file_name FROM users WHERE user_id = ?',
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
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
