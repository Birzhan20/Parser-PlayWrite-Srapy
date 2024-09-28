import scrapy

class KithSpider(scrapy.Spider):
    name = 'kith_spider_man'
    allowed_domains = ['kith.com']
    start_urls = ['https://kith.com/pages/shop-mens'] # Департамент для парсинга

    def parse(self, response, **kwargs):
        # Извлекаются все ссылки shop all из подразделов департамента
        shop_all_links = response.css('a.site-header__grandchild-link[aria-label="Shop All"]::attr(href)').getall()

        for link in shop_all_links:
            full_link = response.urljoin(link)
            yield scrapy.Request(url=full_link, callback=self.parse_shop_all)

    # Сам процесс парсинга по css элемантам в рамках цикла выше
    def parse_shop_all(self, response, **kwargs):

        products = response.css('div.product-card')

        for product in products:
            yield {
                'title': product.css('h1.product-card__title::text').get(),
                'price': product.css('span[aria-label="current price"]::text').get(),
                'link': response.urljoin(product.css('a::attr(href)').get()),
                'image': product.css('img::attr(src)').get()
            }

        # Переход пагинации если оно есть
        next_page = response.css('a.next::attr(href)').get()
        if next_page:
            yield scrapy.Request(response.urljoin(next_page), callback=self.parse)