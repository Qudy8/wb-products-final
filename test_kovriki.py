"""Поиск ковриков в Excel"""
from excel_helper import ExcelHelper

excel_path = "user_files/701912845_сomission.xlsx"

helper = ExcelHelper(excel_path)
data = helper.load_data()

print("Поиск всех ключей с 'коврик' в Excel:\n")
print("=" * 80)

found = []
for key, value in data.items():
    if 'коврик' in key or 'ковр' in key:
        found.append((key, value))
        print(f"Ключ: '{key}'")
        print(f"  Категория: {value['category']}")
        print(f"  Предмет: {value['subject']}")
        print()

if not found:
    print("❌ Ничего не найдено с 'коврик'")

print("=" * 80)
print(f"\nВсего найдено: {len(found)}")

# Тестируем разные варианты поиска
print("\n" + "=" * 80)
print("Тест разных вариантов поиска:")
print("=" * 80)

test_variants = [
    'Коврик для ванной',
    'коврик для ванной',
    'Коврики для ванной',
    'коврики для ванной',
    'коврик для ванны',
    'коврики для ванны',
]

for variant in test_variants:
    result = helper.find_by_subject(variant)
    status = "✅" if result else "❌"
    print(f"{status} '{variant}'")
    if result:
        print(f"   Нашел: {result['subject']}")
