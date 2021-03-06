#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import click
import datetime

from watchlist import app, db
from watchlist.models import User, arXivEmail


@app.cli.command()  # 注册为命令
@click.option('--drop', is_flag=True, help='Create after drop.')
# 设置选项
def initdb(drop):
    """Initialize the database."""
    if drop:  # 判断是否输入了选项
        db.drop_all()
    db.create_all()

    user = User(email=os.environ.get('EMAIL1'))
    user.set_password(os.environ.get('PASSWORD'))
    db.session.add(user)

    user = User(email=os.environ.get('EMAIL2'))
    user.set_password(os.environ.get('PASSWORD'))
    db.session.add(user)

    user = User(email=os.environ.get('EMAIL3'))
    user.set_password(os.environ.get('PASSWORD'))
    db.session.add(user)

    db.session.commit()
    click.echo('Initialized database.')  # 输出提示信息


@app.cli.command()  # 减一天
# 设置选项
def deleteoneday():
    arxivemails = arXivEmail.query.all()
    for arxivemail in arxivemails:
        arXivEmail.query.filter(arXivEmail.id == arxivemail.id).update({
            "lastTracktime":
            arxivemail.lastTracktime - datetime.timedelta(days=1)
        })
        db.session.commit()
    click.echo('Update database.')  # 输出提示信息
