# -*- coding: utf-8 -*-
import json

import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem

STATES = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA',
          'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
          'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
          'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
          'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']

DAY_MAPPING = [
    "Mo",
    "Tu",
    "We",
    "Th",
    "Fr",
    "Sa",
    "Su"
]

URL = 'https://insomniacookies.com/locations/searchStores'


class InsomniaCookiesSpider(scrapy.Spider):
    name = "insomnia_cookies"
    allowed_domains = ['insomniacookies.com']
    start_urls = ['https://insomniacookies.com/locations']
    download_delay = 0.3

    def start_requests(self):
        url = URL

        headers = {
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://insomniacookies.com',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': 'https://insomniacookies.com/locations',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        }

        for state in STATES:
            form_data = {'state': state}

            yield scrapy.http.FormRequest(url=url, method='POST', formdata=form_data, headers=headers,
                                          callback=self.parse)

    def parse_hours(self, store_data):
        opening_hours = OpeningHours()

        for day in DAY_MAPPING:
            open_time = store_data["store_info"]["store_open"]
            close_time = store_data["store_info"]["store_close"]
            if open_time and close_time:
                # Handle inconsistent time formats
                if open_time.count(':') == 1:
                    open_time = ':00 '.join(open_time.split())
                if close_time.count(':') == 1:
                    close_time = ':00 '.join(close_time.split())

                opening_hours.add_range(day=day, open_time=open_time.strip(), close_time=close_time.strip(),
                                        time_format='%I:%M:%S %p')

        return opening_hours.as_opening_hours()

    def parse(self, response):

        data = json.loads(response.body_as_unicode())
        stores = data["stores"]

        if stores:
            for store in stores:

                properties = {
                    'name': store["store_info"]["name"].strip(),
                    'ref': store["store_info"]["id"],
                    'addr_full': store["store_info"]["address"].strip(),
                    'city': store["store_info"]["city"].strip(),
                    'state': store["store_info"]["state"].strip(),
                    'postcode': store["store_info"]["zip"].strip(),
                    'phone': store["store_info"].get("phone"),
                    'website': response.url,
                    'lat': float(store["store_info"]["store_lat"]),
                    'lon': float(store["store_info"]["store_lon"])
                }

                hours = self.parse_hours(store)
                if hours:
                    properties["opening_hours"] = hours

                yield GeojsonPointItem(**properties)