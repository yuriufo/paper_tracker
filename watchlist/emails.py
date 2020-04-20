#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

from threading import Thread

from watchlist import app, mail

from flask import render_template
from flask_mail import Message


def _send_async_mail(message):
    with app.app_context():
        mail.send(message)


def send_message(to, subject, sender, template, **kwargs):
    message = Message(subject, sender=sender, recipients=[to])
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
