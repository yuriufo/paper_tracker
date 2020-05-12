#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import urllib.request
import feedparser

import datetime
from collections import OrderedDict
from pathlib import Path

from watchlist import logger

# logging.basicConfig(format='%(asctime)s - %(filename)s[line:%(lineno)d] - '
#                     '%(levelname)s: %(message)s',
#                     level=logging.INFO,
#                     filename="log.log",
#                     filemode="w")
# logger = logging.getLogger(__name__)


class arXiv(object):
    base_url = 'http://export.arxiv.org/api/query?'

    def __init__(self,
                 max_index=None,
                 start_index=0,
                 sort_by='lastUpdatedDate',
                 sort_order='descending',
                 results_per_iteration=10,
                 time_sleep=2):
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

    def get_search_query(self, Subject_Category, keyword, author):
        search_query = []
        # 构造作者请求参数
        if isinstance(author, (tuple, list)):
            search_query.append(r"%28{0}%29".format("+OR+".join(
                ["au:%22" + au + "%22" for au in author])))
        elif isinstance(author, str) and len(author) > 0:
            search_query.append(r"%28{0}%29".format("au:%22" + author + "%22"))

        # 构造类别请求参数
        if len(Subject_Category) > 0:
            search_query.append(r"%28{0}%29".format("+OR+".join(
                ["cat:" + sc for sc in Subject_Category])))

        # 构造关键词请求参数
        if isinstance(keyword, (tuple, list)):
            search_query.append(r"%28{0}%29".format(
                "+OR+".join(["ti:%22" + kw + "%22"
                             for kw in keyword]) + "+OR+" +
                "+OR+".join(["abs:%22" + kw + "%22" for kw in keyword])))
        elif isinstance(keyword, str) and len(keyword) > 0:
            search_query.append(
                r"%28{0}%29".format("ti:%22" + keyword + "%22+OR+abs:%22" +
                                    keyword + "%22"))

        # 构造搜索请求参数
        search_query = "+AND+".join(search_query)
        logger.info('Searching arXiv for {0}'.format(search_query))

        return search_query.replace(' ', '+')

    def search(self,
               Subject_Category,
               keyword,
               author,
               period=7,
               max_ind=None):
        search_query = self.get_search_query(Subject_Category, keyword, author)
        timeNow = datetime.datetime.strptime(str(datetime.date.today()),
                                             '%Y-%m-%d')

        result = OrderedDict()

        max_index = max_ind if max_ind is not None else self.max_index
        # 开始跟踪论文
        num_added_total = 0
        for i in range(self.start_index, max_index,
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
                j['_version'] = f'version: v{version}'

                # 若结果中没有这篇论文，则添加
                if rawid not in result:
                    tmp = OrderedDict()
                    for i in ("title", "authors", "published", "updated",
                              "updated_parsed", "summary", "link",
                              'arxiv_comment'):
                        if i == 'authors':
                            tmp[i] = ', '.join([aut['name'] for aut in j[i]])
                        elif i == 'arxiv_comment':
                            if 'arxiv_comment' in j:
                                tmp[i] = j[i].replace("\n ",
                                                      "").replace("\n", "")
                            else:
                                tmp[i] = ""
                        elif i == 'link':
                            tmp[i] = j[i]
                            tmp['pdf'] = j[i].replace("abs", "pdf")
                        elif isinstance(j[i], str):
                            tmp[i] = j[i].replace("\n ", "").replace("\n", "")
                        else:
                            tmp[i] = j[i]

                    # 检查时间，默认一星期内
                    tempTime = datetime.datetime.strptime(
                        tmp['updated'].split('T')[0], r'%Y-%m-%d')
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

    # def dump_db(self, Subject_Category, keyword):
    #     db_name = f'{Subject_Category}-{keyword}'

    #     search_query = self.get_search_query(Subject_Category, keyword)

    #     # 若存在数据库则加载
    #     try:
    #         with open(self.db_path + '\\' + db_name + '.json', 'r') as f:
    #             db = json.load(f, object_hook=OrderedDict)
    #     except Exception as e:
    #         logger.error('error loading existing database:')
    #         logger.error(e)
    #         logger.error('starting from an empty database')
    #         db = OrderedDict()

    #     # 开始跟踪论文
    #     logger.info('database has {0} entries at start'.format(len(db)))
    #     num_added_total = 0
    #     for i in range(self.start_index, self.max_index,
    #                    self.results_per_iteration):
    #         logger.info("Results {0} - {1}".format(
    #             i, i + self.results_per_iteration))

    #         query = 'search_query={0}&sortBy={1}&sortOrder={2}&start={3}&max_results={4}'.format(
    #             search_query, self.sort_by, self.sort_order, i,
    #             self.results_per_iteration)

    #         for _ in range(5):
    #             try:
    #                 with urllib.request.urlopen(url=self.base_url + query,
    #                                             timeout=5.0) as url:
    #                     response = url.read()
    #                 parse = feedparser.parse(response)
    #                 break
    #             except Exception as e:
    #                 logger.error(e)
    #         else:
    #             logger.error('Get response error.')
    #             break

    #         num_added = 0
    #         num_skipped = 0
    #         for e in parse.entries:
    #             j = self.encode_feedparser_dict(e)

    #             # 提取某篇论文的raw arxiv id和version
    #             rawid, version = self.parse_arxiv_url(j['id'])
    #             j['_version'] = version

    #             # 若数据库中没有这篇论文或版本更新，则添加或更新数据库
    #             if rawid not in db or j['_version'] > db[rawid]['_version']:
    #                 tmp = OrderedDict()
    #                 for i in ("title", "author", "published", "updated",
    #                           "summary", "link", "_version"):
    #                     if isinstance(j[i], str):
    #                         tmp[i] = j[i].replace("\n ", "").replace("\n", "")
    #                     else:
    #                         tmp[i] = j[i]
    #                 db[rawid] = tmp
    #                 logger.info('Updated %s added %s' %
    #                             (j['updated'].encode('utf-8'),
    #                              j['title'].encode('utf-8')))
    #                 num_added += 1
    #                 num_added_total += 1
    #             else:
    #                 num_skipped += 1

    #         logger.info('Added {0} papers, already had {1}.'.format(
    #             num_added, num_skipped))

    #         if len(parse.entries) == 0:
    #             logger.info(
    #                 'Received no results from arxiv. Exiting. Restart later maybe.'
    #             )
    #             break

    #         # logger.info('Sleeping for {0} seconds'.format(self.time_sleep))
    #         time.sleep(self.time_sleep)

    #     # 若有新论文，则更新数据库
    #     if num_added_total > 0:
    #         logger.info('Saving database with {0} papers to {1}'.format(
    #             len(db), self.db_path + '\\' + db_name + '.json'))
    #         items = sorted(db.items(),
    #                        key=lambda obj: obj[1]["updated"],
    #                        reverse=True)
    #         new_db = OrderedDict()
    #         for item in items:
    #             new_db[item[0]] = db[item[0]]

    #         with open(self.db_path + '\\' + db_name + '.json', 'w') as f:
    #             json.dump(new_db, f, indent=4)


if __name__ == "__main__":
    cpath = Path.cwd()
    dbpath = cpath / 'db'
    ar = arXiv(results_per_iteration=20)
