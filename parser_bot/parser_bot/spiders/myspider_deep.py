import scrapy

"""Парсит в глубину все карточки товара что есть на сайте"""


class KithSpider(scrapy.Spider):
    name = 'kith_deep'
    allowed_domains = ['kith.com']
    start_urls = [
        'https://kith.com/pages/shop-mens',
        'https://kith.com/pages/shop-womens',
        'https://kith.com/pages/shop-kids',
        'https://kith.com/collections/kith-baby',
                  ]  # Департамент для парсинга

    def parse(self, response, **kwargs):
        # Извлекаются все ссылки "Shop All" из подразделов департамента
        shop_all_links = response.css('a.site-header__grandchild-link[aria-label="Shop All"]::attr(href)').getall()

        for link in shop_all_links:
            full_link = response.urljoin(link)
            yield scrapy.Request(url=full_link, callback=self.parse_shop_all)

    # Процесс парсинга продуктов из подразделов
    def parse_shop_all(self, response, **kwargs):
        products = response.css('div.product-card')

        for product in products:
            product_link = response.urljoin(product.css('a::attr(href)').get())

            # Переход на карточку продукта для дальнейшего парсинга
            yield scrapy.Request(url=product_link, callback=self.parse_product_details)

        # Переход по страницам пагинации, если есть
        next_page = response.css('a.next::attr(href)').get()
        if next_page:
            yield scrapy.Request(response.urljoin(next_page), callback=self.parse_shop_all)

    # Парсинг подробностей на странице продукта
    def parse_product_details(self, response):
        product = response.css('div.product__shop')
        for item in product:
            yield {
                'title': self.clean_text(response.css('h1.product__title *::text').get()),

                'color': self.clean_text(item.css('h2.product__color::text').get()),

                # с элемента <span> берет цену
                'price': self.clean_text(item.css('span[aria-label="current price"]::text').get()),

                # списком собирает <label> с класса product-swatch__label
                'size': [self.clean_text(size) for size in response.css('label.product-swatch__label::text').getall()],

                #  * извлекает текст из все дочерних элементов <span>, <p> и тд.
                'description': self.clean_text(' '.join(
                    item.css('div.product__editors-note__content *::text').getall()
                )),

                #  списком собирает все <p> из класса product-description и через генератор списка чистится от пробелов
                'details': [
                    self.clean_text(detail) for detail in response.css('div.product-description p::text').getall()
                ],

                'link': response.url,

                'image': response.css('img::attr(src)').get(),
            }

    # Функция для очистки текста от лишних пробелов и символов
    def clean_text(self, text):
        if text:
            return ' '.join(text.split())
        return None
