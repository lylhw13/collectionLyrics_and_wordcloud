# -*- coding: utf-8 -*-
import scrapy
import urllib.parse
from scrapy.http import Request

import codecs
from selenium import webdriver
import time

from scrapy import signals

from collectionLyrics.items import CollectionlyricsItem

import re

class CollyricsSpider(scrapy.Spider):
    name = 'colLyrics'
    allowed_domains = ['y.qq.com']
    singers = ["周杰伦"]
    #start_urls = ['http://y.qq.com/']

    def __init__(self):
        self.browser = self.initBrowser()
        super(CollyricsSpider, self).__init__()
        self.fo = codecs.open('song_list.txt', 'w', 'utf-8')
        self.fo_error = open('error_urls.txt', 'w')
        self.fo_no_copyright = open('no_copy_right.txt', 'w')   # 一些页面qq音乐没有版权，将信息记录
        self.page_content_urls = []

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(CollyricsSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_closed(self):
        print("spider closed")
        self.browser.quit()
        self.fo.close()
        self.fo_error.close()
        self.fo_no_copyright.close()

    def initBrowser(self):
        options = webdriver.ChromeOptions()
        # options.binary_location = 'D:/Python/tools/chromedriver.exe'
        # options.add_argument('headless')  # NO GUI
        options.add_argument('lang=zh_CN.UTF-8')  # setting language
        # options.add_argument('--no-sandbox')      # bypass os security model
        # options.add_argument('--disable-dev-shm-usage')

        # disable cookies
        options.add_experimental_option('prefs', {"profile.default_content_settings.cookies": 2})

        # change headers
        options.add_argument(
            'user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36"')

        browser = webdriver.Chrome(executable_path='D:/Python/tools/chromedriver.exe', chrome_options=options) # windows
        # browser = webdriver.Chrome(executable_path='/usr/local/bin/chromedriver', chrome_options=options)  # centos
        # brower.implicitly_wait(600) #implicit wait seconds

        print('init browser')
        return browser

    def start_requests(self):
        base_url = "https://y.qq.com/portal/search.html#page=1&searchid=1&remoteplace=txt.yqq.top&t=song&w="
        for singer in self.singers:
            url = base_url + urllib.parse.quote(singer)
            yield Request(url=url, meta={'singer':singer}, callback=self.parse)

    def parse(self, response):
        singer = response.meta.get('singer')
        page_index = re.match(r'.*#page=(\d+)&.*', response.url).group(1)

        items = response.xpath("//div[@class='mod_songlist']/ul[@class='songlist__list']/li")
        print("current url {0}".format(response.url))

        self.fo.write("{0}  page:{1}\n".format('*' * 30, page_index))
        for index, item in enumerate(items):
            name_url_selector = item.xpath(
                "./div/div[@class='songlist__songname']/span[@class='songlist__songname_txt']")

            try:
                name = name_url_selector.xpath("./a/@title").extract()[0]
                url = name_url_selector.xpath("./a/@href").extract()[0]

                message = "{0:5}   {1:16}   {2}\n".format(index+1, name, url)
                print(message)
                self.fo.write(message)
                self.page_content_urls.append((url, index + 1, page_index))

            except Exception:
                message = "the {0:3} item has error at page {1:3}\n".format(index + 1, page_index)
                print(message)
                self.fo_error.write(message)

        try:
            self.browser.find_element_by_xpath("//a[@class='next js_pageindex']").click()
            time.sleep(5)
            yield Request(url=self.browser.current_url, meta={'singer': singer}, callback=self.parse, dont_filter=True)
        except Exception:
            for content_url, item_index, page_index in self.page_content_urls:
                time.sleep(10)
                yield Request(url=content_url, meta={'singer': singer, 'item_index': item_index,
                                                 'page_index': page_index}, callback=self.parse_content)

    def parse_content(self, response):
        song_item = CollectionlyricsItem()
        song_item['target_singer'] = response.meta.get('singer')
        song_item['page_index'] = response.meta.get('page_index')
        song_item['item_index'] = response.meta.get('item_index')
        song_item['url'] = response.url

        # check this song whether has copyright
        song_copyright = response.xpath("//div[@class='none_txt']/p/text()").extract()
        if len(song_copyright) != 0:
            print(song_copyright[0])
            message = "page {0:3} item {1:3} has no copy right url {2}\n".format(
                song_item['page_index'], song_item['item_index'], song_item['url'])
            print(message)
            self.fo_no_copyright.write(message)
            return

        song_detail = response.xpath("//div[@class='main']/div[@class='mod_data']/div[@class='data__cont']")
        try:
            song_item['title'] = song_detail.xpath("//h1[@class='data__name_txt']/@title").extract()[0]
            song_item['singer'] = song_detail.xpath("./div[@class='data__singer']/@title").extract()[0]
            song_item['album'] = song_detail.xpath(
                "./ul[@class='data__info']/li[@class='data_info__item data_info__item--even']/a/text()").extract()[0]
            song_item['date'] = song_detail.xpath("./ul[@class='data__info']/li[@class='data_info__item js_public_time']/text()").extract()[0]
            song_item['lyric'] = response.xpath("//div[@class='lyric__cont_box']/p/text()").extract()
            yield song_item

        except Exception:
            message = "page {0:3} item {1:3} has content error url {2}\n".format(
                song_item['page_index'], song_item['item_index'], song_item['url'])
            print(message)
            self.fo_error.write(message)