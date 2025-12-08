"""Модуль для работы с платежами через ЮKassa"""
import uuid
import logging
from typing import Optional, Dict, Any
from yookassa import Configuration, Payment
from yookassa.domain.notification import WebhookNotification
from yookassa.domain.common import SecurityHelper
import config

# Настройка логирования
logger = logging.getLogger(__name__)

# Инициализация ЮKassa
if config.YUKASSA_SHOP_ID and config.YUKASSA_SECRET_KEY:
    Configuration.account_id = config.YUKASSA_SHOP_ID
    Configuration.secret_key = config.YUKASSA_SECRET_KEY
    logger.info(f"ЮKassa инициализирована. Тестовый режим: {config.YUKASSA_TEST_MODE}")
else:
    logger.warning("ЮKassa не настроена: отсутствуют YUKASSA_SHOP_ID или YUKASSA_SECRET_KEY")


class YuKassaPayment:
    """Класс для работы с платежами ЮKassa"""

    @staticmethod
    def create_payment(
        amount: str,
        description: str,
        user_id: int,
        return_url: str,
        save_payment_method: bool = True,
        payment_method_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Создание платежа в ЮKassa

        Args:
            amount: Сумма платежа (например, "599.00")
            description: Описание платежа
            user_id: ID пользователя Telegram
            return_url: URL для возврата после оплаты
            save_payment_method: Сохранять ли платежный метод для автоплатежей
            payment_method_id: ID сохраненного платежного метода (для автоплатежей)

        Returns:
            Dict с информацией о платеже или None в случае ошибки
        """
        try:
            # Генерируем уникальный ключ идемпотентности
            idempotence_key = str(uuid.uuid4())

            # Формируем параметры платежа
            payment_data = {
                "amount": {
                    "value": amount,
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": return_url
                },
                "capture": True,  # Автоматическое подтверждение платежа
                "description": description,
                "metadata": {
                    "user_id": str(user_id)
                }
            }

            # Если нужно сохранить платежный метод
            if save_payment_method and not payment_method_id:
                payment_data["save_payment_method"] = True

            # Если используется сохраненный платежный метод
            if payment_method_id:
                payment_data["payment_method_id"] = payment_method_id

            # Создаем платеж
            payment = Payment.create(payment_data, idempotence_key)

            logger.info(f"Создан платеж {payment.id} для пользователя {user_id}")

            return {
                "id": payment.id,
                "status": payment.status,
                "amount": payment.amount.value,
                "currency": payment.amount.currency,
                "description": payment.description,
                "confirmation_url": payment.confirmation.confirmation_url if payment.confirmation else None,
                "created_at": payment.created_at.isoformat() if payment.created_at else None,
                "paid": payment.paid,
                "test": payment.test
            }

        except Exception as e:
            logger.error(f"Ошибка создания платежа: {e}")
            return None

    @staticmethod
    def get_payment(payment_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение информации о платеже

        Args:
            payment_id: ID платежа в ЮKassa

        Returns:
            Dict с информацией о платеже или None
        """
        try:
            payment = Payment.find_one(payment_id)

            result = {
                "id": payment.id,
                "status": payment.status,
                "amount": payment.amount.value,
                "currency": payment.amount.currency,
                "description": payment.description,
                "paid": payment.paid,
                "test": payment.test,
                "created_at": payment.created_at.isoformat() if payment.created_at else None,
                "metadata": payment.metadata if payment.metadata else {}
            }

            # Добавляем информацию о платежном методе, если есть
            if payment.payment_method:
                result["payment_method"] = {
                    "type": payment.payment_method.type,
                    "id": payment.payment_method.id,
                    "saved": payment.payment_method.saved if hasattr(payment.payment_method, 'saved') else False,
                    "title": payment.payment_method.title if hasattr(payment.payment_method, 'title') else None
                }

                # Для банковских карт добавляем детали
                if payment.payment_method.type == "bank_card" and hasattr(payment.payment_method, 'card'):
                    result["payment_method"]["card"] = {
                        "first6": payment.payment_method.card.first6 if hasattr(payment.payment_method.card, 'first6') else None,
                        "last4": payment.payment_method.card.last4,
                        "expiry_month": payment.payment_method.card.expiry_month,
                        "expiry_year": payment.payment_method.card.expiry_year,
                        "card_type": payment.payment_method.card.card_type
                    }

            return result

        except Exception as e:
            logger.error(f"Ошибка получения платежа {payment_id}: {e}")
            return None

    @staticmethod
    def cancel_payment(payment_id: str) -> bool:
        """
        Отмена платежа

        Args:
            payment_id: ID платежа в ЮKassa

        Returns:
            True если платеж отменен успешно
        """
        try:
            idempotence_key = str(uuid.uuid4())
            payment = Payment.cancel(payment_id, idempotence_key)

            logger.info(f"Платеж {payment_id} отменен")
            return payment.status == "canceled"

        except Exception as e:
            logger.error(f"Ошибка отмены платежа {payment_id}: {e}")
            return False

    @staticmethod
    def verify_webhook_signature(request_body: str, signature: str) -> bool:
        """
        Проверка подписи webhook-уведомления от ЮKassa

        Args:
            request_body: Тело запроса (JSON string)
            signature: Подпись из заголовка

        Returns:
            True если подпись валидна
        """
        try:
            return SecurityHelper().is_signature_valid(signature, request_body)
        except Exception as e:
            logger.error(f"Ошибка проверки подписи webhook: {e}")
            return False

    @staticmethod
    def parse_webhook_notification(request_body: dict) -> Optional[Dict[str, Any]]:
        """
        Парсинг webhook-уведомления от ЮKassa

        Args:
            request_body: Тело запроса (dict)

        Returns:
            Dict с информацией о событии или None
        """
        try:
            notification = WebhookNotification(request_body)
            payment = notification.object

            result = {
                "type": notification.event,
                "payment_id": payment.id,
                "status": payment.status,
                "amount": payment.amount.value,
                "currency": payment.amount.currency,
                "paid": payment.paid,
                "test": payment.test,
                "metadata": payment.metadata if payment.metadata else {}
            }

            # Добавляем информацию о платежном методе
            if payment.payment_method:
                result["payment_method"] = {
                    "type": payment.payment_method.type,
                    "id": payment.payment_method.id,
                    "saved": payment.payment_method.saved if hasattr(payment.payment_method, 'saved') else False
                }

                if payment.payment_method.type == "bank_card" and hasattr(payment.payment_method, 'card'):
                    result["payment_method"]["card"] = {
                        "first6": payment.payment_method.card.first6 if hasattr(payment.payment_method.card, 'first6') else None,
                        "last4": payment.payment_method.card.last4,
                        "expiry_month": payment.payment_method.card.expiry_month,
                        "expiry_year": payment.payment_method.card.expiry_year,
                        "card_type": payment.payment_method.card.card_type
                    }

            return result

        except Exception as e:
            logger.error(f"Ошибка парсинга webhook: {e}")
            return None


# Экспортируем класс
__all__ = ['YuKassaPayment']
