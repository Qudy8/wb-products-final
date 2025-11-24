"""Тестовый скрипт для проверки структуры данных WB API"""
import asyncio
import json
from wb_api import WildberriesAPI


async def test_structure():
    """Проверяем структуру данных от обоих API"""

    api_key = input("Введите ваш WB API ключ: ")
    wb_api = WildberriesAPI(api_key)

    print("\n" + "="*80)
    print("1. DISCOUNTS API - Получение списка товаров")
    print("="*80)

    # Получаем список товаров
    result = await wb_api.get_goods_list(limit=2)

    if result['success']:
        data = result['data']
        goods = data.get('data', {}).get('listGoods', [])

        if goods:
            print(f"\nНайдено товаров: {len(goods)}")
            print("\nСтруктура первого товара:")
            print(json.dumps(goods[0], indent=2, ensure_ascii=False))

            # Выводим все ключи
            print("\n" + "-"*80)
            print("Все доступные поля товара:")
            print("-"*80)
            for key in sorted(goods[0].keys()):
                print(f"  • {key}: {type(goods[0][key]).__name__}")

            # Проверяем наличие категории и предмета
            first_product = goods[0]
            print("\n" + "-"*80)
            print("Поиск категории и предмета:")
            print("-"*80)

            fields_to_check = [
                'category', 'categoryName', 'categoryID',
                'subject', 'subjectName', 'subjectID',
                'object', 'objectName', 'objectID',
                'brand', 'brandName',
                'vendorCode', 'nmID'
            ]

            for field in fields_to_check:
                if field in first_product:
                    print(f"  ✓ {field}: {first_product[field]}")

            # Получаем nmID для Cards API
            nm_id = first_product.get('nmID')

            if nm_id:
                print("\n" + "="*80)
                print("2. CARDS API - Детальная информация о товаре")
                print("="*80)

                cards_result = await wb_api.get_cards_detail([nm_id])

                if cards_result['success']:
                    cards_data = cards_result['data']
                    products = cards_data.get('data', {}).get('products', [])

                    if products:
                        print(f"\nНайдено товаров: {len(products)}")
                        print("\nСтруктура первого товара:")
                        print(json.dumps(products[0], indent=2, ensure_ascii=False))

                        # Выводим все ключи
                        print("\n" + "-"*80)
                        print("Все доступные поля товара:")
                        print("-"*80)
                        for key in sorted(products[0].keys()):
                            print(f"  • {key}: {type(products[0][key]).__name__}")

                        # Проверяем наличие категории и предмета
                        card_product = products[0]
                        print("\n" + "-"*80)
                        print("Поиск категории и предмета:")
                        print("-"*80)

                        for field in fields_to_check:
                            if field in card_product:
                                print(f"  ✓ {field}: {card_product[field]}")
                    else:
                        print("❌ Товары не найдены в Cards API")
                else:
                    print(f"❌ Ошибка Cards API: {cards_result['error']}")
        else:
            print("❌ Товары не найдены")
    else:
        print(f"❌ Ошибка: {result['error']}")

    print("\n" + "="*80)
    print("Тестирование завершено")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_structure())
