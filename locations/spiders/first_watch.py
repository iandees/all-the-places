# -*- coding: utf-8 -*-
import json
import re
from urllib.parse import urlencode

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class FirstWatchSpider(scrapy.Spider):
    name = "first_watch"
    item_attributes = {'brand': "First Watch"}
    allowed_domains = ["firstwatch.com"]

    def start_requests(self):
        url = "https://www.firstwatch.com/api/get_locations.php?"

        with open('./locations/searchable_points/us_centroids_50mile_radius.csv') as points:
            next(points)
            for point in points:
                _, lat, lon = point.strip().split(',')

                params = {
                    'latitude': '{}'.format(lat),
                    'longitude': '{}'.format(lon)
                }

                yield scrapy.http.Request(url + urlencode(params), callback=self.parse)

    def parse(self, response):
        data = json.loads(response.body_as_unicode())
        website_url = "https://www.firstwatch.com/locations/"

        for place in data:
            properties = {
                'ref': place["id"],
                'name': place["name"],
                'addr_full': place["address"],
                'city': place["city"],
                'state': place["state"],
                'postcode': place["zip"],
                'country': "US",
                'lat': place["latitude"],
                'lon': place["longitude"],
                'phone': place["phone"],
                'website': website_url + place["slug"]
            }

            yield GeojsonPointItem(**properties)
