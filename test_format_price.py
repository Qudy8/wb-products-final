# -*- coding: utf-8 -*-
import sys
import io

# Исправляем кодировку для Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def format_price(price: float) -> str:
    """Форматирует цену: если копейки .00, то не показываем их"""
    if price == int(price):
        return f"{int(price)}"
    else:
        return f"{price:.2f}"

print("=" * 60)
print("ТЕСТ ФУНКЦИИ format_price()")
print("=" * 60)

test_prices = [
    46000.00,   # Целое число с .00
    29440.00,   # Целое число с .00
    14350.00,   # Целое число с .00
    8724.00,    # Целое число с .00
    143.50,     # С копейками
    87.24,      # С копейками
    1234.56,    # С копейками
    5000.0,     # Целое
    99.99,      # С копейками
]

for price in test_prices:
    formatted = format_price(price)
    print(f"{price:>10.2f} ₽  →  {formatted:>10} ₽")

print("\n" + "=" * 60)
print("ПРИМЕРЫ ИЗ РЕАЛЬНЫХ ТОВАРОВ:")
print("=" * 60)

print("\nТовар 1: Автомобильный надувной матрас")
print(f"  Базовая цена: {format_price(46000.00)} ₽")
print(f"  Цена на сайте: {format_price(29440.00)} ₽")

print("\nТовар 2: Коврик для ванной")
print(f"  Базовая цена: {format_price(14350.00)} ₽")
print(f"  Цена на сайте: {format_price(8724.00)} ₽")

print("\nТовар с копейками (пример):")
print(f"  Базовая цена: {format_price(1234.56)} ₽")
print(f"  Цена на сайте: {format_price(987.65)} ₽")
