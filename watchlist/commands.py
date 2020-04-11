#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import click

from watchlist import app, db
from watchlist.models import User


@app.cli.command()  # 注册为命令
@click.option('--drop', is_flag=True, help='Create after drop.')
# 设置选项
def initdb(drop):
    """Initialize the database."""
    if drop:  # 判断是否输入了选项
        db.drop_all()
    db.create_all()

    user = User(email=os.environ.get('EMAIL'))
    user.set_password(os.environ.get('PASSWORD'))
    db.session.add(user)
    db.session.commit()
    click.echo('Initialized database.')  # 输出提示信息
