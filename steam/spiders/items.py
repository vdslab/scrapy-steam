# -*- coding: utf-8 -*-
import os
import json
import scrapy
import requests
from datetime import date, datetime, timedelta

class ItemsSpider(scrapy.Spider):
    name = "items"
    # allowed_domains = ["api.twitch.tv"]
    # start_urls = ["https://api.twitch.tv"]

    def __init__(self, target_date=None, *args, **kwargs):
        super(ItemsSpider, self).__init__(*args, **kwargs)
        if target_date:
            self.target_date = target_date
        else:
            self.target_date = date.today().strftime('%y-%m-%d')

    @ classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(ItemsSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.engine_stopped,
                                signal=scrapy.signals.engine_stopped)
        return spider

    def parse(self, response):
        pass
