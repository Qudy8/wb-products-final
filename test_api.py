"""Тестовый скрипт для проверки WB API"""
import asyncio
import aiohttp
import json


async def test_wb_api():
    """Тестирование разных вариантов запроса к WB API"""

    # Замените на ваш реальный API ключ
    API_KEY = input("Введите ваш WB API ключ: ")

    url = 'https://discounts-prices-api.wildberries.ru/api/v2/list/goods/filter'

    # Разные варианты headers для тестирования
    header_variants = [
        ("Authorization: API_KEY", {'Authorization': API_KEY, 'Content-Type': 'application/json'}),
        ("Authorization: Bearer API_KEY", {'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'}),
        ("Authorization без Content-Type", {'Authorization': API_KEY}),
    ]

    # Разные варианты payload для тестирования
    payload_variants = [
        ("Пустой объект", {}),
        ("С limit и offset", {"limit": 100, "offset": 0}),
        ("С filterNmID", {"filterNmID": []}),
    ]

    async with aiohttp.ClientSession() as session:
        success = False

        for header_name, headers in header_variants:
            if success:
                break

            print(f"\n{'#'*60}")
            print(f"Тестируем headers: {header_name}")
            print(f"{'#'*60}")

            for payload_name, payload in payload_variants:
                print(f"\n{'='*60}")
                print(f"Payload: {payload_name}")
                print(f"Data: {json.dumps(payload, ensure_ascii=False)}")
                print(f"{'='*60}")

                try:
                    async with session.post(url, headers=headers, json=payload) as response:
                        print(f"Статус: {response.status}")
                        response_text = await response.text()

                        if response.status == 200:
                            data = await response.json()
                            print(f"\n🎉 УСПЕХ! 🎉")
                            print(f"Рабочая комбинация:")
                            print(f"  Headers: {header_name}")
                            print(f"  Payload: {payload_name}")
                            print(f"\nПолучено товаров: {len(data.get('data', {}).get('listGoods', []))}")
                            print(f"Первые 2 товара:")
                            for item in data.get('data', {}).get('listGoods', [])[:2]:
                                print(f"  - nmID: {item.get('nmID')}, vendorCode: {item.get('vendorCode')}")
                            success = True
                            break
                        else:
                            print(f"❌ Ошибка: {response_text}")

                except Exception as e:
                    print(f"❌ Исключение: {str(e)}")

        if not success:
            print(f"\n{'!'*60}")
            print("Ни один вариант не сработал. Возможные причины:")
            print("1. API ключ неправильный или не имеет нужных прав")
            print("2. Endpoint требует другие параметры")
            print("3. Нужна другая документация API")
            print(f"{'!'*60}")

    print(f"\n{'='*60}")
    print("Тестирование завершено")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(test_wb_api())
