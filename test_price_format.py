# -*- coding: utf-8 -*-
import sys
import io

# Исправляем кодировку для Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 80)
print("АНАЛИЗ ФОРМАТА ЦЕН ИЗ WB API")
print("=" * 80)

# Примеры из реальных API ответов
examples = [
    {
        'name': 'Товар 1: Автомобильный надувной матрас (619635379)',
        'basic_raw': 4600000,
        'product_raw': 2944000,
        'price_discounts_api': 46000  # из Discounts API (копейки)
    },
    {
        'name': 'Товар 2: Коврик для ванной (35546310)',
        'basic_raw': 1435000,
        'product_raw': 872400,
        'price_discounts_api': 14350  # из Discounts API (копейки)
    }
]

print("\nИССЛЕДУЕМ РАЗНЫЕ ВАРИАНТЫ ПРЕОБРАЗОВАНИЯ:\n")

for ex in examples:
    print(f"\n{ex['name']}")
    print("-" * 80)

    basic_raw = ex['basic_raw']
    product_raw = ex['product_raw']
    price_disc = ex['price_discounts_api']

    print(f"Сырые данные Cards API:")
    print(f"  basic (raw): {basic_raw}")
    print(f"  product (raw): {product_raw}")
    print(f"\nСырые данные Discounts API:")
    print(f"  price: {price_disc}")

    print(f"\nВарианты преобразования Cards API:")
    print(f"  ÷ 100:    basic={basic_raw/100:.2f}, product={product_raw/100:.2f}")
    print(f"  ÷ 1000:   basic={basic_raw/1000:.2f}, product={product_raw/1000:.2f}")
    print(f"  ÷ 10000:  basic={basic_raw/10000:.2f}, product={product_raw/10000:.2f}")

    print(f"\nВарианты преобразования Discounts API:")
    print(f"  ÷ 100:    price={price_disc/100:.2f}")

    # Проверяем какой вариант совпадает
    print(f"\n✅ ПРАВИЛЬНОЕ ПРЕОБРАЗОВАНИЕ:")
    if basic_raw / 100 == price_disc / 100:
        print(f"  Cards API ÷ 100 = Discounts API ÷ 100")
        print(f"  Цена: {price_disc/100:.2f} ₽")
    else:
        print(f"  Cards API: basic={basic_raw/100:.2f} ₽, product={product_raw/100:.2f} ₽")
        print(f"  Discounts API: {price_disc/100:.2f} ₽")
        print(f"  ⚠️ НЕ СОВПАДАЮТ! Cards API нужно делить на {basic_raw / price_disc}")

print("\n" + "=" * 80)
print("ВЫВОД:")
print("=" * 80)
print("Cards API возвращает цены в 'копейках * 100'")
print("Discounts API возвращает цены в 'копейках'")
print("\nДля правильного отображения:")
print("  • Cards API: делить на 100 (получаем рубли)")
print("  • Discounts API: делить на 100 (получаем рубли)")
print("=" * 80)
