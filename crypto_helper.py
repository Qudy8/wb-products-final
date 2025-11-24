"""Модуль для шифрования API ключей"""
from cryptography.fernet import Fernet
from config import ENCRYPTION_KEY
import base64
import os


class CryptoHelper:
    """Класс для шифрования и дешифрования API ключей"""

    def __init__(self):
        """Инициализация с ключом шифрования"""
        # Если ключ не задан в .env, генерируем новый
        if ENCRYPTION_KEY:
            self.key = ENCRYPTION_KEY.encode()
        else:
            # Генерируем новый ключ и сохраняем в файл .env
            self.key = Fernet.generate_key()
            self._save_key_to_env(self.key.decode())

        self.cipher = Fernet(self.key)

    def _save_key_to_env(self, key: str):
        """Сохраняет ключ в .env файл если его там нет"""
        env_path = '.env'

        # Проверяем существует ли файл
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Если ключа нет, добавляем
            if 'ENCRYPTION_KEY' not in content:
                with open(env_path, 'a', encoding='utf-8') as f:
                    f.write(f'\nENCRYPTION_KEY={key}\n')
        else:
            # Создаем новый .env файл
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(f'ENCRYPTION_KEY={key}\n')

    def encrypt(self, text: str) -> str:
        """
        Шифрует текст

        Args:
            text: текст для шифрования

        Returns:
            Зашифрованный текст в base64
        """
        if not text:
            return text

        encrypted_bytes = self.cipher.encrypt(text.encode())
        return encrypted_bytes.decode()

    def decrypt(self, encrypted_text: str) -> str:
        """
        Дешифрует текст

        Args:
            encrypted_text: зашифрованный текст в base64

        Returns:
            Расшифрованный текст
        """
        if not encrypted_text:
            return encrypted_text

        try:
            decrypted_bytes = self.cipher.decrypt(encrypted_text.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            print(f"Ошибка дешифрования: {e}")
            return None
