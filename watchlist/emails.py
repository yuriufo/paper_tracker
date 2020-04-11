#!/usr/bin/env python
# -*- coding: utf-8 -*-

import Thread
import datetime

from watchlist import app, mail

from flask import render_template
from flask_mail import Message


def _send_async_mail(message):
    with app.app_context():
        mail.send(message)


def send_message(to, subject, sender, template, **kwargs):
    message = Message(subject, sender, recipients=[to])
    message.html = render_template(f'{template}.html', **kwargs)
    thr = Thread(target=_send_async_mail, args=[message])
    thr.start()
    return thr


def send_confirm_email(user, token, to=None):
    send_message(subject='Email Confirm',
                 sender='yuri<{0}>'.format(app.config['MAIL_USERNAME']),
                 to=to or user.email,
                 template='confirm',
                 user=user,
                 token=token)


# def send_papers(form_arg, to=None):
#     # send_papers(form_arg, to=current_user.email)
#     send_message(subject='paper tracker {0}'.format(datetime.date.today()),
#                  sender='yuri<{0}>'.format(app.config['MAIL_USERNAME']),
#                  to=to,
#                  template='email',
#                  form_arg=form_arg)

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
# with app.app_context():
#     mail.send(msg)
# flash('邮件发送成功')