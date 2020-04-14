#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

from threading import Thread

from watchlist import app, mail, logging

from flask import render_template
from flask_mail import Message


def _send_async_mail(message):
    with app.app_context():
        mail.send(message)


def send_message(to, subject, sender, template, **kwargs):
    message = Message(subject, sender=sender, recipients=[to])
    logging.info(kwargs.keys())
    with app.app_context():
        message.html = render_template('{0}.html'.format(template), **kwargs)
    thr = Thread(target=_send_async_mail, args=[message])
    thr.start()
    return thr


def send_papers(to, **kwargs):
    # send_papers(form_arg, to=current_user.email)
    send_message(to=to,
                 subject='paper tracker {0}'.format(datetime.date.today()),
                 sender=("yuri", app.config['MAIL_USERNAME']),
                 template='email',
                 **kwargs)


# msg = Message(
#     'paper tracker {0}'.format(datetime.date.today()),
#     sender='yuri<{0}>'.format(app.config['MAIL_USERNAME']),
#     recipients=[current_user.email])
# result_dict, num = arx.search(**form_arg)
# msg.html = render_template('email.html',
#                            result_dict=result_dict,
#                            num=num,
#                            form_arg=form_arg,
#                            SC_name=SC_name,
#                            time=str(datetime.date.today()))
# send_papers(to=email,
#             result_dict=result_dict,
#             num=num,
#             form_arg=form_arg,
#             SC_name=SForm.get_sc_name(subjectcategory),
#             time=str(datetime.date.today()))
# with app.app_context():
#     mail.send(msg)
# flash('邮件发送成功')