"""Модуль для работы с Wildberries API"""
import aiohttp
import ssl
import requests
from typing import Dict, List
from config import WB_API_DISCOUNTS_URL


class WildberriesAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            'Authorization': api_key,
            'Content-Type': 'application/json'
        }

    async def get_goods_list(self, limit: int = 1000, offset: int = 0) -> Dict:
        """
        Получение списка товаров с ценами и скидками
        GET https://discounts-prices-api.wildberries.ru/api/v2/list/goods/filter

        Args:
            limit: количество товаров на странице (макс 1000)
            offset: смещение относительно первого элемента

        Returns:
            Словарь с данными о товарах
        """
        url = f'{WB_API_DISCOUNTS_URL}/api/v2/list/goods/filter'

        # Query параметры
        params = {
            'limit': limit,
            'offset': offset
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=self.headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'success': True,
                            'data': data
                        }
                    else:
                        error_text = await response.text()
                        return {
                            'success': False,
                            'error': f'Ошибка API {response.status}: {error_text}'
                        }
        except Exception as e:
            return {
                'success': False,
                'error': f'Ошибка соединения: {str(e)}'
            }

    def _get_cards_detail_sync(self, nm_ids: List[int]) -> Dict:
        """
        Синхронный метод для получения данных от Cards API через requests
        """
        url = 'https://card.wb.ru/cards/v2/detail'

        nm_string = ';'.join(map(str, nm_ids))
        params = {
            'appType': 1,
            'curr': 'rub',
            'dest': -1257786,
            'spp': 30,
            'nm': nm_string
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*'
        }

        try:
            response = requests.get(url, params=params, headers=headers, verify=False, timeout=30)
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text[:200]}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Connection error: {str(e)}'
            }

    async def get_cards_detail(self, nm_ids: List[int]) -> Dict:
        """
        Async wrapper для получения данных от Cards API

        Args:
            nm_ids: список nmId товаров

        Returns:
            Словарь с детальной информацией о товарах
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_cards_detail_sync, nm_ids)
