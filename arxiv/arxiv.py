#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import json
import urllib.request
import feedparser
import logging

from datetime import datetime
from collections import OrderedDict
from pathlib import Path

logging.basicConfig(format='%(asctime)s - %(filename)s[line:%(lineno)d] - '
                    '%(levelname)s: %(message)s',
                    level=logging.INFO,
                    filename="log.log",
                    filemode="w")
logger = logging.getLogger(__name__)


class Arxiv(object):
    base_url = 'http://export.arxiv.org/api/query?'

    def __init__(self,
                 db_path=None,
                 max_index=None,
                 start_index=0,
                 sort_by='lastUpdatedDate',
                 sort_order='descending',
                 results_per_iteration=10,
                 time_sleep=2):
        self.db_path = db_path
        self.sort_by = sort_by
        self.sort_order = sort_order
        self.results_per_iteration = results_per_iteration
        self.time_sleep = time_sleep
        self.max_index = max_index
        self.start_index = start_index

        if self.max_index is None:
            logger.info('max_index defaulting to inf.')
            self.max_index = 7777777

    def encode_feedparser_dict(self, d):
        if isinstance(d, feedparser.FeedParserDict) or isinstance(d, dict):
            j = {}
            for k in d.keys():
                j[k] = self.encode_feedparser_dict(d[k])
            return j
        elif isinstance(d, list):
            ll = []
            for k in d:
                ll.append(self.encode_feedparser_dict(k))
            return ll
        else:
            return d

    def parse_arxiv_url(self, url):
        ix = url.rfind('/')
        idversion = url[ix + 1:]
        parts = idversion.split('v')
        assert len(parts) == 2, 'error parsing url ' + url
        return parts[0], int(parts[1])

    def get_search_query(self, Subject_Category, keyword):
        # 构造类别请求参数
        if len(Subject_Category) > 0:
            search_query1 = r"%28{0}%29".format("+OR+".join(
                ["cat:" + sc for sc in Subject_Category]))
        else:
            search_query1 = ""

        # 构造关键词请求参数
        if isinstance(keyword, (tuple, list)):
            search_query2 = r"%28{0}%29".format(
                "ti:%22" + "+".join([kw for kw in keyword]) +
                "%22+OR+abs:%22" + "+".join([kw for kw in keyword]) + "%22")
        elif isinstance(keyword, str):
            search_query2 = r"%28{0}%29".format("ti:" + keyword + "+OR+abs:" +
                                                keyword)
        else:
            search_query2 = ""

        # 构造搜索请求参数
        if search_query1 == "" or search_query2 == "":
            search_query = search_query1 + search_query2
        else:
            search_query = "+AND+".join([search_query1, search_query2])
        logger.info('Searching arXiv for {0}'.format(search_query))

        return search_query

    def search(self, Subject_Category, keyword, period=7):
        search_query = self.get_search_query(Subject_Category, keyword)
        timeNow = datetime.now()
        result = OrderedDict()

        # 开始跟踪论文
        num_added_total = 0
        for i in range(self.start_index, self.max_index,
                       self.results_per_iteration):
            logger.info("Results {0} - {1}".format(
                i, i + self.results_per_iteration))

            query = 'search_query={0}&sortBy={1}&sortOrder={2}&start={3}&max_results={4}'.format(
                search_query, self.sort_by, self.sort_order, i,
                self.results_per_iteration)

            for _ in range(5):
                try:
                    with urllib.request.urlopen(url=self.base_url + query,
                                                timeout=5.0) as url:
                        response = url.read()
                    parse = feedparser.parse(response)
                    break
                except Exception as e:
                    logger.error(e)
            else:
                logger.error('Get response error.')
                break

            for e in parse.entries:
                j = self.encode_feedparser_dict(e)

                # 提取某篇论文的raw arxiv id和version
                rawid, version = self.parse_arxiv_url(j['id'])
                j['_version'] = version

                # 若结果中没有这篇论文，则添加
                if rawid not in result:
                    tmp = OrderedDict()
                    for i in ("title", "author", "published", "updated",
                              "summary", "link", "_version"):
                        if isinstance(j[i], str):
                            tmp[i] = j[i].replace("\n ", "").replace("\n", "")
                        else:
                            tmp[i] = j[i]
                    # 检查时间，默认一星期内
                    tempTime = datetime.strptime(tmp['updated'],
                                                 r'%Y-%m-%dT%H:%M:%SZ')
                    if (timeNow - tempTime).days > period:
                        return result, num_added_total

                    result[rawid] = tmp
                    logger.info('Get: %s , title: %s' %
                                (j['updated'].encode('utf-8'),
                                 j['title'].encode('utf-8')))
                    num_added_total += 1

            if len(parse.entries) == 0:
                logger.info(
                    'Received no results from arxiv. Exiting. Restart later maybe.'
                )
                break

            # logger.info('Sleeping for {0} seconds'.format(self.time_sleep))
            time.sleep(self.time_sleep)

        return result, num_added_total

    def dump_db(self, Subject_Category, keyword):
        db_name = f'{Subject_Category}-{keyword}'

        search_query = self.get_search_query(Subject_Category, keyword)

        # 若存在数据库则加载
        try:
            with open(self.db_path + '\\' + db_name + '.json', 'r') as f:
                db = json.load(f, object_hook=OrderedDict)
        except Exception as e:
            logger.error('error loading existing database:')
            logger.error(e)
            logger.error('starting from an empty database')
            db = OrderedDict()

        # 开始跟踪论文
        logger.info('database has {0} entries at start'.format(len(db)))
        num_added_total = 0
        for i in range(self.start_index, self.max_index,
                       self.results_per_iteration):
            logger.info("Results {0} - {1}".format(
                i, i + self.results_per_iteration))

            query = 'search_query={0}&sortBy={1}&sortOrder={2}&start={3}&max_results={4}'.format(
                search_query, self.sort_by, self.sort_order, i,
                self.results_per_iteration)

            for _ in range(5):
                try:
                    with urllib.request.urlopen(url=self.base_url + query,
                                                timeout=5.0) as url:
                        response = url.read()
                    parse = feedparser.parse(response)
                    break
                except Exception as e:
                    logger.error(e)
            else:
                logger.error('Get response error.')
                break

            num_added = 0
            num_skipped = 0
            for e in parse.entries:
                j = self.encode_feedparser_dict(e)

                # 提取某篇论文的raw arxiv id和version
                rawid, version = self.parse_arxiv_url(j['id'])
                j['_version'] = version

                # 若数据库中没有这篇论文或版本更新，则添加或更新数据库
                if rawid not in db or j['_version'] > db[rawid]['_version']:
                    tmp = OrderedDict()
                    for i in ("title", "author", "published", "updated",
                              "summary", "link", "_version"):
                        if isinstance(j[i], str):
                            tmp[i] = j[i].replace("\n ", "").replace("\n", "")
                        else:
                            tmp[i] = j[i]
                    db[rawid] = tmp
                    logger.info('Updated %s added %s' %
                                (j['updated'].encode('utf-8'),
                                 j['title'].encode('utf-8')))
                    num_added += 1
                    num_added_total += 1
                else:
                    num_skipped += 1

            logger.info('Added {0} papers, already had {1}.'.format(
                num_added, num_skipped))

            if len(parse.entries) == 0:
                logger.info(
                    'Received no results from arxiv. Exiting. Restart later maybe.'
                )
                break

            # logger.info('Sleeping for {0} seconds'.format(self.time_sleep))
            time.sleep(self.time_sleep)

        # 若有新论文，则更新数据库
        if num_added_total > 0:
            logger.info('Saving database with {0} papers to {1}'.format(
                len(db), self.db_path + '\\' + db_name + '.json'))
            items = sorted(db.items(),
                           key=lambda obj: obj[1]["updated"],
                           reverse=True)
            new_db = OrderedDict()
            for item in items:
                new_db[item[0]] = db[item[0]]

            with open(self.db_path + '\\' + db_name + '.json', 'w') as f:
                json.dump(new_db, f, indent=4)


if __name__ == "__main__":
    cpath = Path.cwd()
    dbpath = cpath / 'db'
    ar = Arxiv(db_path=str(dbpath), results_per_iteration=20)
    res, _ = ar.search(("cs.CR", "cs.SE"), "malware", 30)