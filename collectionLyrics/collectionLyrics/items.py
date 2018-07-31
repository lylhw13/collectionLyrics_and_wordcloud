# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class CollectionlyricsItem(scrapy.Item):
    # define the fields for your item here like:
    target_singer = scrapy.Field()
    singer = scrapy.Field()
    title = scrapy.Field()
    album = scrapy.Field()
    date = scrapy.Field()
    lyric = scrapy.Field()
    page_index = scrapy.Field()
    item_index = scrapy.Field()
    url = scrapy.Field()
