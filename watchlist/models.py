#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from watchlist import app, db


class User(db.Model, UserMixin):  # 表名将会是 user（自动生成，小写处理）
    email = db.Column(db.String(50), primary_key=True)  # 邮箱, 主键
    password_hash = db.Column(db.String(128))  # 密码哈希

    # confirmed = db.Column(db.Boolean, default=False)

    # def generate_confirmation_token(self, expiration=3600):
    #     s = Serializer(app.config['SECRET_KEY'], expiration)
    #     return s.dumps({'confirm': self.email})

    # @staticmethod
    # def check_activate_token(self, token):
    #     s = Serializer(app.config['SECRET_KEY'])
    #     try:
    #         data = s.loads(token)  # 解码
    #     except Exception:
    #         return False
    #     user = User.query.get(email=data.get('confirm'))
    #     if user is None:
    #         return False
    #     if not user.confirmed:
    #         user.confirmed = True
    #         db.session.add(user)
    #     return True

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return self.email


class arXivEmail(db.Model):  # 表名将会是 email（自动生成，小写处理）
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 主键
    email = db.Column(db.String(50), db.ForeignKey('user.email'))  # 邮箱, 设置外键
    keyword = db.Column(db.Text())  # 关键字
    author = db.Column(db.Text())  # 作者
    subjectcategory = db.Column(db.Text(), nullable=False)  # 主题
    period = db.Column(db.Integer(), nullable=False)  # 检测时段
    lastTracktime = db.Column(db.DateTime,
                              default=datetime.datetime.now,
                              nullable=False)
