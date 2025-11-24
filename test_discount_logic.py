"""
Тестовый скрипт для проверки новой логики расчета скидок
"""
# -*- coding: utf-8 -*-
import sys
import io

# Исправляем кодировку для Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Тестовые данные из реальных API запросов

# Товар 1: 619635379 (Автомобильный надувной матрас)
print("=" * 60)
print("Товар 1: 619635379 (Автомобильный надувной матрас)")
print("=" * 60)

# Данные из Discounts API
seller_discount_1 = 0  # discount в Discounts API
price_api_1 = 46000  # price в копейках

# Данные из Cards API
basic_price_raw_1 = 4600000  # basic в копейках * 100
product_price_raw_1 = 2944000  # product в копейках * 100

# Преобразуем в рубли
basic_price_1 = basic_price_raw_1 / 100
product_price_1 = product_price_raw_1 / 100

print(f"Базовая цена (Cards API): {basic_price_1:.2f} ₽")
print(f"Цена на сайте (Cards API): {product_price_1:.2f} ₽")
print(f"Скидка продавца (Discounts API): {seller_discount_1}%")

# Рассчитываем скидку на сайте
site_discount_1 = ((basic_price_1 - product_price_1) / basic_price_1) * 100
print(f"\nСкидка на сайте: {site_discount_1:.1f}%")

# Реальная скидка
real_discount_1 = site_discount_1 - seller_discount_1
print(f"Реальная скидка: {real_discount_1:.1f}%")
print(f"Проходит фильтр ≥28%: {'✅ ДА' if real_discount_1 >= 28 else '❌ НЕТ'}")

print("\n" + "=" * 60)
print("Товар 2: 35546310 (Коврик для ванной)")
print("=" * 60)

# Данные из Discounts API
seller_discount_2 = 5  # discount в Discounts API
price_api_2 = 14350  # price в копейках
discounted_price_api_2 = 13632.5  # discountedPrice в копейках

# Данные из Cards API
basic_price_raw_2 = 1435000  # basic в копейках * 100
product_price_raw_2 = 872400  # product в копейках * 100

# Преобразуем в рубли
basic_price_2 = basic_price_raw_2 / 100
product_price_2 = product_price_raw_2 / 100

print(f"Базовая цена (Cards API): {basic_price_2:.2f} ₽")
print(f"Цена на сайте (Cards API): {product_price_2:.2f} ₽")
print(f"Скидка продавца (Discounts API): {seller_discount_2}%")

# Рассчитываем скидку на сайте
site_discount_2 = ((basic_price_2 - product_price_2) / basic_price_2) * 100
print(f"\nСкидка на сайте: {site_discount_2:.1f}%")

# Реальная скидка
real_discount_2 = site_discount_2 - seller_discount_2
print(f"Реальная скидка: {real_discount_2:.1f}%")
print(f"Проходит фильтр ≥28%: {'✅ ДА' if real_discount_2 >= 28 else '❌ НЕТ'}")

print("\n" + "=" * 60)
print("Итоговая статистика:")
print("=" * 60)
print(f"Товар 1: реальная скидка {real_discount_1:.1f}% - {'подходит' if real_discount_1 >= 28 else 'не подходит'}")
print(f"Товар 2: реальная скидка {real_discount_2:.1f}% - {'подходит' if real_discount_2 >= 28 else 'не подходит'}")
