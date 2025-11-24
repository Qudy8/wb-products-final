"""Тест Cards API с конкретными nmID из бота"""
import requests
import json

# ID товаров из бота
nm_ids = [565612891, 273007147, 17731671, 405689272]

url = 'https://card.wb.ru/cards/v2/detail'

# Разные варианты параметров
params_variants = [
    ("Вариант 1: только nm и curr", {
        'nm': ';'.join(map(str, nm_ids)),
        'curr': 'rub'
    }),
    ("Вариант 2: nm, curr, spp=0", {
        'nm': ';'.join(map(str, nm_ids)),
        'curr': 'rub',
        'spp': 0
    }),
    ("Вариант 3: nm, curr, spp=30", {
        'nm': ';'.join(map(str, nm_ids)),
        'curr': 'rub',
        'spp': 30
    }),
    ("Вариант 4: все параметры как раньше", {
        'nm': ';'.join(map(str, nm_ids)),
        'curr': 'rub',
        'spp': 30,
        'appType': 1,
        'dest': -1257786
    }),
    ("Вариант 5: один ID для теста", {
        'nm': str(nm_ids[0]),
        'curr': 'rub',
        'spp': 0
    }),
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': '*/*'
}

print(f"Тестируем nmID: {nm_ids}\n")
print("="*80)

for variant_name, params in params_variants:
    print(f"\n{variant_name}")
    print(f"Параметры: {params}")
    print("-"*80)

    try:
        response = requests.get(url, params=params, headers=headers, verify=False, timeout=30)
        print(f"Статус: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            products = data.get('data', {}).get('products', [])
            print(f"✅ Получено товаров: {len(products)}")

            if products:
                print(f"\n🎉 УСПЕХ! Рабочий вариант: {variant_name}")
                print(f"\n📋 ПОЛНАЯ СТРУКТУРА ПЕРВОГО ТОВАРА:")
                first = products[0]
                print(json.dumps(first, indent=2, ensure_ascii=False))

                # Выводим все полученные ID
                all_ids = [p.get('id') for p in products]
                print(f"\n✅ Все полученные ID: {all_ids}")

                # Ищем цены в структуре
                print(f"\n🔍 Поиск цен в структуре:")
                print(f"  salePriceU: {first.get('salePriceU')}")
                print(f"  priceU: {first.get('priceU')}")

                # Проверяем sizes
                if 'sizes' in first and first['sizes']:
                    print(f"\n  sizes[0]: {json.dumps(first['sizes'][0], indent=4, ensure_ascii=False)}")

                break
            else:
                print("❌ Массив products пуст")
                # Показываем структуру ответа
                print(f"Ключи в data: {list(data.get('data', {}).keys())}")
        else:
            print(f"❌ Ошибка HTTP: {response.status_code}")
            print(f"Ответ: {response.text[:200]}")

    except Exception as e:
        print(f"❌ Исключение: {str(e)}")

print("\n" + "="*80)
print("Тестирование завершено")
