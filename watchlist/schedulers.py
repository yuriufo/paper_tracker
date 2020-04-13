#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime

from watchlist import db, logger

from watchlist.forms import SForm

from watchlist.models import arXivEmail

from watchlist.emails import send_papers

from arxiv.arxiv import arXiv

arx = arXiv(results_per_iteration=10, time_sleep=0.5)


def task_daily():
    arxivemails = arXivEmail.query.all()
    logger.info('arXivEmail: {0} items.'.format(arxivemails.count()))

    timeNow = datetime.now()
    for arxivemail in arxivemails:
        email = arxivemail.email
        keyword = arxivemail.keyword
        author = arxivemail.author
        subjectcategory = arxivemail.subjectcategory
        period = arxivemail.period
        lastTracktime = arxivemail.lastTracktime
        if (timeNow - lastTracktime).days < period:
            continue

        try:
            keyword = eval(keyword)
        except Exception:
            logger.exception('eval(keyword) faild: {0}'.format(keyword))
        try:
            author = eval(author)
        except Exception:
            logger.exception('eval(author) faild: {0}'.format(author))
        try:
            subjectcategory = eval(subjectcategory)
        except Exception:
            logger.exception(
                'eval(subjectcategory) faild: {0}'.format(subjectcategory))
            continue
        try:
            result_dict, num = arx.search(Subject_Category=subjectcategory,
                                          keyword=keyword,
                                          author=author,
                                          period=period)
            if num > 0:
                form_arg = {
                    "Subject_Category": subjectcategory,
                    "keyword": keyword,
                    "author": author,
                    "period": period
                }
                send_papers(to=email,
                            result_dict=result_dict,
                            num=num,
                            form_arg=form_arg,
                            SC_name=SForm.get_sc_name(subjectcategory),
                            time=str(datetime.date.today()))
        except Exception:
            logger.exception('search or send email faild.')
            continue

        arXivEmail.query.filter(arXivEmail.id == arxivemail.id).update(
            {"lastTracktime": datetime.datetime.now()})
        db.session.commit()

        logger.info(f"send: {email} - {keyword} - {author} - {period} - {lastTracktime}")