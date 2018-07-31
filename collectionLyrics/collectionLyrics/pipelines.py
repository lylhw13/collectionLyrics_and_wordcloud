# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy import signals
from scrapy.exceptions import DropItem
import MySQLdb


import re
import codecs

class CollectionlyricsPipeline(object):
    def __init__(self):
        self.conn = MySQLdb.connect(host='127.0.0.1', user='root', passwd='root', db='collection_lyrics', charset='utf8')
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        # handle the date
        re_date_result = re.match(r'.*?(\d+-\d+-\d+)', item['date'])        # ?限定前面为非贪婪模式
        if re_date_result:
            release_date = re_date_result.group(1)
        else:
            release_date = "1111-11-11"

        # handle the lyric
        lyric = ' '.join(item['lyric']).strip()

        # classify
        re_classify_result = re.search(item['target_singer'], item['singer'])

        if re_classify_result:
            table_name = "jay_lyrics"
            file_name = './jay_lyrics/{}.txt'.format(item['title'])
        else:
            table_name = "other_lyrics"
            file_name = './other_lyrics/{}.txt'.format(item['title'])

        insert_sql = "insert into {0}(title, singer, album, date, page_index, item_index, lyric)" \
                     " VALUES (%s, %s, %s, %s, %s, %s, %s)".format(table_name)  #format 不转义%

        self.cursor.execute(insert_sql, (item['title'], item['singer'], item['album'],
                                         release_date, item['page_index'], item['item_index'], lyric))
        self.conn.commit()

        with codecs.open(file_name, 'w', 'utf-8') as f:
            if not re_classify_result:
                f.write("page {0:3} item {1:3} url {2} \n".format(item['page_index'], item['item_index'], item['url']))
            f.write("title：{0}\nsinger：{1}\nalbum：{2}\ndate：{3}\n\n\n".format(
                    item['title'], item['singer'], item['album'], item['date']))
            f.write(lyric)

        return item

class JSMainPageDuplicatesPipeline(object):
    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):

        if item['id'] in self.ids_seen:
            raise DropItem("Duplicate item found: %s" % item)

        else:
            self.ids_seen.add(item['id'])
            return item