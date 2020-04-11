#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json

from flask import request, render_template
from flask import url_for, redirect, flash

from flask_login import current_user
from flask_login import login_user, logout_user, login_required

from watchlist import app, db, logger
from watchlist.models import User, arXivEmail
from watchlist.forms import UserForm, SForm


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', form=SForm())


@app.route('/arxiv', methods=['GET', 'POST'])
def arxiv():
    global arx
    if request.method == 'POST':  # 判断是否是 POST 请求
        try:
            form = SForm(formdata=request.form)
            if form.validate():
                form_arg = form.get_arg()
                SC_name = form_arg.pop("Subject_Category_name")
                fc = form_arg.pop("function")

                if fc == 0:  # 预览
                    result_dict, num = arx.search(**form_arg, max_ind=5)
                    return render_template('arxiv.html',
                                           result_dict=result_dict,
                                           num=num,
                                           form_arg=form_arg,
                                           SC_name=SC_name)
                elif not current_user.is_authenticated:
                    flash('Login firstly.')
                    return redirect(url_for('login'))
                else:
                    arxivemail = arXivEmail(
                        email=current_user.email,
                        arg_dict=json.dumps(form_arg))  # json.loads()
                    db.session.add(arxivemail)
                    db.session.commit()
                    flash('监控添加成功')
                    return redirect(url_for('index'))
            else:
                flash('Form verification failed.')
                return render_template('index.html', form=form)
        except Exception:
            logger.exception('Faild.')
            flash('Get a Exception.')

    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':  # 判断是否是 POST 请求
        try:
            form = UserForm(formdata=request.form)
            if not form.validate():
                flash('Invalid input!')
                return render_template('register.html', form=form)

            email = form.email.data
            password = form.password.data
            password_valid = form.password_valid.data

            if not (len(email) <= 50 and 8 <= len(password) <= 20):
                flash('Invalid input!')
                return redirect(url_for('register'))

            if password != password_valid:
                flash('Password is inconsistent!')
                return redirect(url_for('register'))

            user = User.query.get(email)
            if user is not None:
                flash('Email exists.')
                return redirect(url_for('register'))

            user = User(email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            flash('Register success.')
            return redirect(url_for('index'))

        except Exception:
            logger.exception('Faild to Register.')
            flash('Get a Exception.')

    return render_template('register.html', form=UserForm())


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':  # 判断是否是 POST 请求
        try:
            form = UserForm(formdata=request.form)
            if not form.validate():
                flash('Invalid input!')
                return render_template('login.html', form=form)

            email = form.email.data
            password = form.password.data

            if not (len(email) <= 50 and 8 <= len(password) <= 20):
                flash('Invalid input!')
                return redirect(url_for('login'))

            user = User.query.get(email)
            if user is None or not user.validate_password(password):
                flash('User does not exist or password is wrong.')
                return redirect(url_for('login'))

            login_user(user)
            flash('Login success.')
            return redirect(url_for('index'))

        except Exception:
            logger.exception('Faild to Login.')
            flash('Get a Exception.')

    return render_template('login.html', form=UserForm())


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout success.')
    return redirect(url_for('index'))


@app.route('/states')
@login_required
def states():
    if current_user.email == os.environ.get('EMAIL'):
        users = User.query.all()
        arxivemails = arXivEmail.query.all()
    else:
        users = User.query.get(current_user.email)
        arxivemails = arXivEmail.query.filter_by(email=current_user.email)

    return render_template('states.html', users=users, arxivemails=arxivemails)
