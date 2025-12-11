"""Модуль автоматического продления подписок"""
import asyncio
import logging
from datetime import datetime, timedelta
from database import Database
from yukassa_payment import YuKassaPayment
from config import SUBSCRIPTION_PLANS
from aiogram import Bot

logger = logging.getLogger(__name__)


class AutoRenewal:
    """Класс для автоматического продления подписок"""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = Database()

    async def process_auto_renewals(self):
        """Обработка автоматического продления истекающих подписок"""
        try:
            # Получаем подписки, истекающие в ближайшие 3 дня
            expiring_subscriptions = await self.db.get_expiring_subscriptions(days_before=3)

            logger.info(f"Найдено {len(expiring_subscriptions)} истекающих подписок")

            for subscription in expiring_subscriptions:
                user_id = subscription['user_id']
                plan_id = subscription['plan_id']
                end_date = datetime.fromisoformat(subscription['end_date'])

                # Проверяем, что подписка истекает через 1 день или меньше
                days_left = (end_date - datetime.now()).days
                if days_left > 1:
                    logger.info(f"Подписка пользователя {user_id} истекает через {days_left} дней, пропускаем")
                    continue

                # Проверяем, не был ли уже создан платеж автопродления в последние 24 часа
                has_recent_payment = await self.db.has_recent_auto_renewal_payment(user_id, hours=24)
                if has_recent_payment:
                    logger.info(f"Для пользователя {user_id} уже создан платеж автопродления в последние 24 часа, пропускаем")
                    continue

                logger.info(f"Попытка автопродления подписки для пользователя {user_id}")

                # Получаем сохраненные платежные методы пользователя
                payment_methods = await self.db.get_user_payment_methods(user_id)

                if not payment_methods:
                    logger.info(f"У пользователя {user_id} нет сохраненных карт, отправляем уведомление")
                    await self.send_renewal_reminder(user_id, end_date, plan_id)
                    continue

                # Берем первую активную карту
                payment_method = payment_methods[0]
                payment_method_id = payment_method['payment_method_id']

                # Получаем план подписки
                plan = SUBSCRIPTION_PLANS.get(plan_id)
                if not plan:
                    logger.error(f"План {plan_id} не найден для пользователя {user_id}")
                    continue

                # Получаем email пользователя
                email = await self.db.get_user_email(user_id)
                if not email:
                    email = f"user{user_id}@telegram.user"

                # Создаем платеж по сохраненной карте
                payment_data = YuKassaPayment.create_payment(
                    amount=plan['price'],
                    description=f"Автопродление: {plan['description']}",
                    user_id=user_id,
                    email=email,
                    return_url=f"https://t.me/productswbbot",
                    save_payment_method=False,
                    payment_method_id=payment_method_id
                )

                if not payment_data:
                    logger.error(f"Ошибка создания платежа для пользователя {user_id}")
                    await self.send_renewal_failed_notification(user_id, end_date)
                    continue

                # Сохраняем платеж в БД
                await self.db.create_payment(
                    user_id=user_id,
                    payment_id=payment_data['id'],
                    plan_id=plan_id,
                    amount=plan['price'],
                    description=f"Автопродление: {plan['description']}",
                    confirmation_url=payment_data.get('confirmation_url', ''),
                    test=payment_data['test']
                )

                # Ждем обработки платежа
                await asyncio.sleep(5)

                # Проверяем статус платежа
                payment_info = YuKassaPayment.get_payment(payment_data['id'])

                if payment_info and payment_info['status'] == 'succeeded' and payment_info['paid']:
                    # Активируем подписку
                    success = await self.db.activate_subscription_yukassa(payment_data['id'])
                    await self.db.update_payment_status(payment_data['id'], 'succeeded', True)

                    if success:
                        logger.info(f"✅ Подписка пользователя {user_id} успешно продлена автоматически")
                        await self.send_renewal_success_notification(user_id)
                    else:
                        logger.error(f"Ошибка активации подписки для пользователя {user_id}")
                        await self.send_renewal_failed_notification(user_id, end_date)
                else:
                    status = payment_info.get('status') if payment_info else 'unknown'
                    logger.warning(f"Автоплатеж для пользователя {user_id} не прошел, статус: {status}")
                    await self.send_renewal_failed_notification(user_id, end_date)

        except Exception as e:
            logger.error(f"Ошибка при обработке автопродлений: {e}", exc_info=True)

    async def send_renewal_reminder(self, user_id: int, end_date: datetime, plan_id: str):
        """Отправка напоминания о необходимости продления подписки"""
        try:
            plan = SUBSCRIPTION_PLANS.get(plan_id, {})
            plan_name = plan.get('name', 'Неизвестный план')

            days_left = (end_date - datetime.now()).days

            await self.bot.send_message(
                user_id,
                f"⚠️ <b>Напоминание о продлении подписки</b>\n\n"
                f"Ваша подписка '{plan_name}' истекает через {days_left} дн.\n"
                f"Дата окончания: {end_date.strftime('%d.%m.%Y')}\n\n"
                f"У вас нет сохраненных карт для автопродления.\n"
                f"Для продления подписки перейдите в '💳 Подписка'",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки напоминания пользователю {user_id}: {e}")

    async def send_renewal_success_notification(self, user_id: int):
        """Уведомление об успешном автопродлении"""
        try:
            subscription = await self.db.get_active_subscription(user_id)
            if subscription:
                end_date = datetime.fromisoformat(subscription['end_date'])

                await self.bot.send_message(
                    user_id,
                    f"✅ <b>Подписка автоматически продлена!</b>\n\n"
                    f"Ваша подписка успешно продлена.\n"
                    f"Действует до: {end_date.strftime('%d.%m.%Y')}\n\n"
                    f"Спасибо, что остаетесь с нами! 🎉",
                    parse_mode="HTML"
                )
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления об успехе пользователю {user_id}: {e}")

    async def send_renewal_failed_notification(self, user_id: int, end_date: datetime):
        """Уведомление о неудачном автопродлении"""
        try:
            days_left = (end_date - datetime.now()).days

            await self.bot.send_message(
                user_id,
                f"❌ <b>Не удалось автоматически продлить подписку</b>\n\n"
                f"Подписка истекает через {days_left} дн.\n"
                f"Дата окончания: {end_date.strftime('%d.%m.%Y')}\n\n"
                f"Возможные причины:\n"
                f"• Недостаточно средств на карте\n"
                f"• Карта заблокирована или истек срок действия\n\n"
                f"Пожалуйста, обновите платежную информацию в разделе '💳 Подписка'",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления о неудаче пользователю {user_id}: {e}")

    async def run_scheduler(self):
        """Запуск планировщика автопродлений (проверка каждые 12 часов)"""
        logger.info("Запущен планировщик автопродлений")

        while True:
            try:
                logger.info("Запуск проверки истекающих подписок...")
                await self.process_auto_renewals()
                logger.info("Проверка завершена")
            except Exception as e:
                logger.error(f"Ошибка в планировщике: {e}", exc_info=True)

            # Ждем 12 часов до следующей проверки
            await asyncio.sleep(12 * 60 * 60)
