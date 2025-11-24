"""Тест загрузки данных из Excel"""
from excel_helper import ExcelHelper

excel_path = "user_files/701912845_сomission.xlsx"

print("Тестирование загрузки Excel файла...\n")

helper = ExcelHelper(excel_path)
data = helper.load_data()

print(f"✅ Загружено записей: {len(data)}")

stats = helper.get_stats()
print(f"✅ Категорий: {stats['total_categories']}")
print(f"✅ Предметов: {stats['total_subjects']}")

print("\nПримеры данных:")
print("=" * 80)

# Показываем первые 5 записей
for idx, (key, value) in enumerate(list(data.items())[:5], 1):
    print(f"\n{idx}. Ключ: '{key}'")
    print(f"   Категория: {value['category']}")
    print(f"   Предмет: {value['subject']}")
    print(f"   WB комиссия: {value['commission_wb']}%")
    print(f"   FBS комиссия: {value['commission_fbs']}%")

print("\n" + "=" * 80)
print("\nТест поиска:")
print("=" * 80)

# Тестируем поиск
test_subjects = ['домкраты', 'багажные боксы', 'вибраторы']

for subject in test_subjects:
    result = helper.find_by_subject(subject)
    if result:
        print(f"\n✅ Найдено '{subject}':")
        print(f"   Категория: {result['category']}")
        print(f"   FBS комиссия: {result['commission_fbs']}%")
    else:
        print(f"\n❌ Не найдено: '{subject}'")
