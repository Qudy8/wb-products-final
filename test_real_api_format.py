# -*- coding: utf-8 -*-
import sys
import io

# Исправляем кодировку для Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 80)
print("АНАЛИЗ РЕАЛЬНЫХ ДАННЫХ ИЗ API")
print("=" * 80)

# Реальные данные из Discounts API (которые мы получили ранее)
discounts_data = [
    {'nmID': 619635379, 'price': 46000, 'discountedPrice': 46000, 'discount': 0},
    {'nmID': 35546310, 'price': 14350, 'discountedPrice': 13632.5, 'discount': 5},
]

# Реальные данные из Cards API
cards_data = [
    {'nmID': 619635379, 'basic': 4600000, 'product': 2944000},
    {'nmID': 35546310, 'basic': 1435000, 'product': 872400},
]

print("\nПРОВЕРЯЕМ СООТВЕТСТВИЕ ЦЕН:\n")

for i, disc in enumerate(discounts_data):
    card = cards_data[i]
    nm_id = disc['nmID']

    print(f"Товар {nm_id}:")
    print(f"  Discounts API: price = {disc['price']}")
    print(f"  Cards API: basic = {card['basic']}")

    # Проверяем разные варианты
    ratio = card['basic'] / disc['price']
    print(f"  Соотношение: {ratio}")

    if ratio == 100:
        print(f"  ✅ Discounts API в РУБЛЯХ, Cards API в копейках×100")
        print(f"     Discounts: {disc['price']} ₽")
        print(f"     Cards: {card['basic']/100} ₽")
    elif ratio == 1:
        print(f"  ✅ Оба API в одинаковом формате")
    else:
        print(f"  ⚠️ Нестандартное соотношение!")

    print()

print("=" * 80)
print("ВЫВОД:")
print("=" * 80)
print("Discounts API: цены в РУБЛЯХ (46000 = 46000 ₽)")
print("Cards API: цены в КОПЕЙКАХ×100 (4600000 / 100 = 46000 ₽)")
print("\nПреобразование:")
print("  • Discounts API: НЕ НУЖНО делить (уже в рублях)")
print("  • Cards API: делить на 100")
print("=" * 80)
