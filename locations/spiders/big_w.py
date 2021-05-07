# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

class BigWSpider(scrapy.Spider):
    name = "big_w"
    allowed_domains = ["bigw.com.au"]
    start_urls = ('https://www.bigw.com.au/sitemap/store-en-aud.xml',)
    days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

    custom_settings = {'DOWNLOAD_DELAY' : 0.5,}
    
    def _parse_hour_str(self, hour_string):
        time_, am_pm = tuple(hour_string.split(" "))
        hour, min = tuple(time_.split(":"))
        hour = int(hour)
        if am_pm == "PM":
            hour += 12
        return f"{hour}:{min}"

    def parse(self, response):
        response.selector.remove_namespaces()
        links = response.xpath("//loc/text()").getall()
        for link in links:
            yield scrapy.Request(link, callback=self.parse_store)

    def parse_hours(self, hours_results):
        opening_hours = OpeningHours()
        for idx, day in enumerate(hours_results[0:7]):
            store_hours = day.strip()
            if "-" not in store_hours or ":" not in store_hours:
                continue
            parts = store_hours.strip().split(" - ")
            open_time = self._parse_hour_str(parts[0])
            close_time = self._parse_hour_str(parts[1])
            opening_hours.add_range(self.days[idx], open_time, close_time)
        
        return opening_hours.as_opening_hours()

    def parse_address(self, address):
        cleaned = [a.strip() for a in address]
        street = cleaned[0]
        suburb, state, postcode = tuple(cleaned[1].split('\xa0'))
        phonenumber = cleaned[3].replace("Ph:","").strip()
        return dict(street=street,
                        city=suburb.strip(),
                        state=state.strip(),
                        postcode=postcode.strip(),
                        phone=phonenumber,
                        country="AU")


    def parse_store(self, response):
        store_name = response.xpath("//h1[@class='blue']/strong/text()").get().replace("BIG W ","")
        hours = self.parse_hours(response.xpath("//div[@id='collapseOne']/div/div/div[contains(@class, 'text-right') and contains(@class, 'col-xs-8')]/text()").getall())
        addresses = self.parse_address(response.xpath("//address/text()").getall())
        lat = response.xpath("//div[@id='map_canvas']/@data-latitude").get()
        lon = response.xpath("//div[@id='map_canvas']/@data-longitude").get()
        geo = dict(lat=lat, lon=lon)
        if float(lat) == 0.0 or float(lon) == 0.0:
            geo = {}
        properties = dict(name=store_name,
                        opening_hours=hours,
                        website=response.url,
                        ref=response.url.split("/")[-2],
                        **addresses,
                        **geo)
        yield GeojsonPointItem(**properties)


