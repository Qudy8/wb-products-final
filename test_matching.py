"""Тест сопоставления предметов"""
from excel_helper import ExcelHelper

excel_path = "user_files/701912845_сomission.xlsx"

print("Тестирование нового поиска с нормализацией...\n")

helper = ExcelHelper(excel_path)

# Тестовые кейсы
test_cases = [
    ('Коврик для ванной', 'Коврики для ванной'),
    ('домкрат', 'домкраты'),
    ('вибратор', 'вибраторы'),
    ('лонгслив', 'лонгсливы'),
    ('футболка', 'футболки'),
]

print("=" * 80)
print("Тест нормализации:")
print("=" * 80)

for wb_name, excel_name in test_cases:
    print(f"\nWB API: '{wb_name}' <-> Excel: '{excel_name}'")

    # Пробуем найти
    result = helper.find_by_subject(wb_name)
    if result:
        print(f"  ✅ Найдено!")
        print(f"     Категория: {result['category']}")
        print(f"     Предмет: {result['subject']}")
        print(f"     FBS комиссия: {result['commission_fbs']}%")
    else:
        print(f"  ❌ Не найдено")

print("\n" + "=" * 80)
print("Проверка реальных данных из Excel:")
print("=" * 80)

# Ищем "коврики для ванной" в данных
data = helper.load_data()
for key in list(data.keys())[:50]:
    if 'коврик' in key:
        print(f"  Найден ключ: '{key}'")
        print(f"    Категория: {data[key]['category']}")
        print(f"    Предмет: {data[key]['subject']}")
