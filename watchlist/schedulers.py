#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

from watchlist import db, logger

from watchlist.forms import SForm

from watchlist.models import arXivEmail

from watchlist.emails import send_papers

from arxiv.arxiv import arXiv

arx = arXiv(results_per_iteration=10, time_sleep=0.5)


def task_daily():
    arxivemails = arXivEmail.query.all()
    logger.info('arXivEmail: {0} items.'.format(len(arxivemails)))

    timeNow = datetime.datetime.now()
    timeNow_date = datetime.datetime.strptime(str(timeNow.date()), '%Y-%m-%d')
    for arxivemail in arxivemails:
        email = arxivemail.email
        keyword = arxivemail.keyword
        author = arxivemail.author
        subjectcategory = arxivemail.subjectcategory
        period = arxivemail.period
        lastTracktime = arxivemail.lastTracktime
        lastTracktime_date = datetime.datetime.strptime(
            str(lastTracktime.date()), '%Y-%m-%d')
        if (timeNow_date - lastTracktime_date).days < period:
            continue

        try:
            keyword = eval(keyword)
        except Exception:
            pass
        try:
            author = eval(author)
        except Exception:
            pass
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
                logger.info(
                    f"send: {email} - {keyword} - {author} - {period} - {lastTracktime}"
                )
        except Exception:
            logger.exception('search or send email faild.')
            continue
        db.session.query(arXivEmail).filter(arXivEmail.id == arxivemail.id).update(
            {"lastTracktime": timeNow})
        db.session.commit()
