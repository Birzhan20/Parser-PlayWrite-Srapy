import asyncio
from playwright.async_api import async_playwright
import re
import json
import os


async def scrape_links_and_get_urls(page, data):

    await page.wait_for_timeout(timeout=1000)

    # Извлекаем все ссылки
    links = await page.locator(
        'div[data-testid="ProductTile"] a[data-testid="productTile-ProductSwitcherLink"]').evaluate_all(
        'elements => elements.map(element => element.href)')

    print(links)

    for link in links:

        await page.goto(link)

        # Ждем, пока скрипт будет добавлен в DOM
        await page.wait_for_selector('script[data-testid="product-schema"]', state='attached')

        # Извлекаем данные из schema
        product_schema = json.loads(
            await (await page.query_selector('script[data-testid="product-schema"]')).inner_text())

        # Обработка размеров
        sizes = []
        id = 1
        try:
            for offer in product_schema.get('offers', {}).get('offers', []):
                sizes.append({
                    'id': id,
                    'name': "US M " + offer.get('description', 'Неизвестно'),
                    'price': offer.get('price', 'Не указано'),
                    'quantity': 1,
                })
                id += 1
        except KeyError:
            sizes.append({
                'id': 'error',
                'name': 'Неизвестно',
                'price': 'Не указано',
                'quantity': 1,
            })
            id += 1

        # Получение остальных данных
        product_data = {
            'id': await page.text_content('p.chakra-text.css-pxl067'),
            'brand': product_schema.get('brand', {}).get('name', 'Adidas'),
            'name': product_schema.get('name', 'Неизвестно'),
            'description': product_schema.get('description', 'Нет описания'),
            'price': product_schema.get('offers', {}).get('lowPrice',
                                                          product_schema.get('offers', {}).get('price', 'Не указано')),
            'currency': product_schema.get('offers', {}).get('priceCurrency', 'USD'),
            'department': 'For Women' if 'women' in product_schema.get('name', '').lower() else 'For Men',
            'category': 'Shoes',
            'subcategory': product_schema.get('brand', {}).get('name', 'Неизвестно'),
            'product_type': product_schema.get('model', '').replace(product_schema.get('brand', {}).get('name', ''),
                                                                    '').strip(),
            'sizes': sizes,
            'images': [product_schema.get('image', '')],
            'url': product_schema.get('url', 'Не указано'),
            'from': 'USA',
            'details': ', '.join(await page.locator('div[data-component="product-trait"]').all_inner_texts()),
            'wearing': "",
            'washing': "",
            'composition': "",
            'store': "Stockx",
            'image': await page.locator('img.chakra-image').nth(0).get_attribute('src'),  # Изображение
            'color': await page.text_content('span[data-component="secondary-product-title"]'),
        }

        # Создание директории, если она не существует
        os.makedirs('jsons', exist_ok=True)

        # Сохранение данных в файл
        sanitized_name = re.sub(r'[\\/*?:"<>|]', '', product_data['name'])  # Убираем недопустимые символы в имени файла
        with open(f"jsons/{sanitized_name}.json", 'w', encoding='utf-8') as json_file:
            json.dump(product_data, json_file, ensure_ascii=False, indent=4)

        print(f"Данные успешно записаны в jsons/{sanitized_name}.json")

    await page.locator('a[aria-label="Next"]').click()


async def main():
    data = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(
            'https://stockx.com/browse/men?brand=adidas&category=shoes')  # Вставьте правильный URL

        await scrape_links_and_get_urls(page, data)

        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
