#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging

import memcache

from flask import Flask

from flask_mail import Mail

from flask_login import LoginManager

from flask_sqlalchemy import SQLAlchemy

from flask_apscheduler import APScheduler

from flask_wtf.csrf import CSRFProtect

logging.basicConfig(format='%(asctime)s - %(filename)s[line:%(lineno)d] - '
                    '%(levelname)s: %(message)s',
                    level=logging.INFO,
                    filename="log.log",
                    filemode="w")
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='./templates')

WIN = sys.platform.startswith('win')
if WIN:  # 如果是 Windows 系统，使用三个斜线
    prefix = 'sqlite:///'
else:  # 否则使用四个斜线
    prefix = 'sqlite:////'

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')  # 电子邮件服务器的主机名或IP地址
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT'))  # 电子邮件服务器的端口
app.config["MAIL_USE_SSL"] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')  # 你的邮件账户用户名
app.config['MAIL_PASSWORD'] = os.environ.get(
    'MAIL_PASSWORD')  # 邮件账户的密码,这个密码是指的是授权码

app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(
    app.root_path, 'db', 'data.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控

mail = Mail(app)
db = SQLAlchemy(app)
scheduler = APScheduler()
scheduler.init_app(app)
login_manager = LoginManager(app)
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'

from watchlist.schedulers import task_daily

scheduler.add_job(func=task_daily,
                  id='cron_task',
                  trigger='cron',
                  hour='1',
                  replace_existing=True)
scheduler.start()

mc = memcache.Client(["127.0.0.1:11211"])

CSRFProtect(app)

@login_manager.user_loader
def load_user(user_email):
    from watchlist.models import User
    user = User.query.get(user_email)
    return user


from watchlist import views, commands
