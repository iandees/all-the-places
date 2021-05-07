# -*- coding: utf-8 -*-
import re
import json
import scrapy

from locations.items import GeojsonPointItem


class ApothekenDESpider(scrapy.Spider):
    name = "apotheken_de"
    allowed_domains = ['apotheken-umschau.de']
    download_delay = 0.5
    start_urls = ("https://www.apotheken-umschau.de/apotheken/deutschland/",)

    def parse_data(self, response):
        data = {}
        data_json = response.xpath(
            '//div[@class="js-googlemaps-emergency"]/@data-results').get()
        if data_json:
            data = json.loads(data_json)

        stores = response.xpath('//div[@class="container-fluid"]')
        for store in stores:
            telephone = fax = None
            title = store.xpath('.//b/text()').get()

            if title:
                try:
                    extra = store.xpath(
                        './/div[@class="col-md-4"]//p/text()'
                    ).getall()
                    for e in extra:
                        match = re.match(r'^Telefon: (.*)$', e)
                        if match:
                            telephone = match.group(1)

                        match = re.match(r'^Fax: (.*)$', e)
                        if match:
                            fax = match.group(1)
                except Exception:
                    pass

                for record in data:
                    if record['name'] == title:
                        properties = {
                            'name': record["name"],
                            'ref': f'{record["lat"]}_{record["lng"]}',
                            'addr_full': record["address"]["street"],
                            'city': record["address"]["city"],
                            'postcode': record["address"]["postalCode"],
                            'country': "DE",
                            'lat': float(record["lat"]),
                            'lon': float(record["lng"]),
                            'phone': telephone,
                            'extras': {
                                'fax': fax
                            }
                        }
                        yield GeojsonPointItem(**properties)

    def parse_zips(self, response):
        zips = response.xpath(
            '//div[@class="copy"]//ul//a/@href'
        ).getall()

        for record in zips:
            yield scrapy.Request(
                response.urljoin(record), callback=self.parse_data
            )

    def parse(self, response):
        zip_range = response.xpath(
            '//div[@class="copy"]//ul//li//a/@href'
        ).getall()

        for record in zip_range:
            yield scrapy.Request(
                response.urljoin(record), callback=self.parse_zips
            )
