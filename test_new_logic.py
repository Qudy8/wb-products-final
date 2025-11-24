# -*- coding: utf-8 -*-
import sys
import io

# Исправляем кодировку для Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 80)
print("НОВАЯ ЛОГИКА РАБОТЫ БОТА")
print("=" * 80)

# Тестовые товары
products = [
    {
        'name': 'Товар 1: Без скидки продавца',
        'basic_cards': 4600000,
        'product_cards': 2944000,
        'discount_seller': 0
    },
    {
        'name': 'Товар 2: Со скидкой продавца 5%',
        'basic_cards': 1435000,
        'product_cards': 872400,
        'discount_seller': 5
    },
    {
        'name': 'Товар 3: Со скидкой продавца 10%',
        'basic_cards': 5000000,
        'product_cards': 2000000,
        'discount_seller': 10
    },
    {
        'name': 'Товар 4: Без скидки на сайте',
        'basic_cards': 3000000,
        'product_cards': 3000000,
        'discount_seller': 0
    },
]

filtered_count = 0
threshold = 28

print(f"\nПорог фильтрации: ≥{threshold}%\n")

for prod in products:
    print(f"\n{prod['name']}")
    print("-" * 80)

    # Преобразуем цены из Cards API
    basic_price = prod['basic_cards'] / 100
    real_price = prod['product_cards'] / 100

    print(f"Базовая цена: {basic_price:.0f} ₽")
    print(f"Цена на сайте: {real_price:.0f} ₽")
    print(f"Скидка продавца: {prod['discount_seller']}%")

    # Рассчитываем скидку на сайте
    if basic_price > 0:
        site_discount = ((basic_price - real_price) / basic_price) * 100
    else:
        site_discount = 0

    # Реальная скидка
    real_discount = site_discount - prod['discount_seller']

    print(f"\n📊 Скидка на сайте: {site_discount:.1f}%")

    if prod['discount_seller'] > 0:
        print(f"🔻 Скидка продавца: {prod['discount_seller']}%")
        print(f"✅ Реальная скидка: {site_discount:.1f}% - {prod['discount_seller']}% = {real_discount:.1f}%")
    else:
        print(f"✅ Реальная скидка: {real_discount:.1f}% (скидки продавца нет)")

    # Проверка фильтра
    if real_discount >= threshold:
        print(f"🟢 ПРОХОДИТ фильтр ≥{threshold}%")
        filtered_count += 1
    else:
        print(f"🔴 НЕ ПРОХОДИТ фильтр ≥{threshold}%")

print("\n" + "=" * 80)
print("ИТОГО:")
print("=" * 80)
print(f"Всего товаров: {len(products)}")
print(f"Подходит по критерию ≥{threshold}%: {filtered_count}")
print(f"Будет показано: {min(filtered_count, 20)}")
