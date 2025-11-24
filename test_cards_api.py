"""Тестовый скрипт для проверки Cards API"""
import asyncio
import aiohttp
import json


async def test_cards_api():
    """Тестирование Cards API для получения реальных цен"""

    # Введите несколько nmId через запятую
    nm_input = input("Введите nmId товаров через запятую (например: 123456,789012): ")
    nm_ids = [int(x.strip()) for x in nm_input.split(',') if x.strip()]

    url = 'https://card.wb.ru/cards/v2/detail'

    # Query параметры
    nm_string = ';'.join(map(str, nm_ids))
    params = {
        'nm': nm_string,
        'curr': 'rub',
        'spp': 0
    }

    print(f"\n{'='*60}")
    print(f"URL: {url}")
    print(f"Params: {params}")
    print(f"{'='*60}\n")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                print(f"Статус: {response.status}")

                if response.status == 200:
                    data = await response.json()
                    print(f"\n✅ УСПЕХ!")
                    print(f"\nПолная структура ответа:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))

                    # Пытаемся найти товары
                    print(f"\n{'='*60}")
                    print("Анализ структуры:")
                    print(f"{'='*60}")

                    if 'data' in data:
                        print(f"✓ Найден ключ 'data'")
                        if 'products' in data['data']:
                            print(f"✓ Найден ключ 'data.products'")
                            products = data['data']['products']
                            print(f"  Количество товаров: {len(products)}")

                            if products:
                                print(f"\n  Первый товар:")
                                first = products[0]
                                print(f"    id: {first.get('id')}")
                                print(f"    salePriceU: {first.get('salePriceU')}")
                                print(f"    priceU: {first.get('priceU')}")
                                print(f"    Реальная цена: {first.get('salePriceU', 0) / 100} ₽")

                else:
                    error_text = await response.text()
                    print(f"❌ Ошибка: {error_text}")

    except Exception as e:
        print(f"❌ Исключение: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_cards_api())
