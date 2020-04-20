#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import string
import random
import datetime

from threading import Thread

from flask import request, render_template
from flask import url_for, redirect, flash, jsonify

from flask_login import current_user
from flask_login import login_user, logout_user, login_required

from watchlist import app, db, logger, mc
from watchlist.models import User, arXivEmail
from watchlist.forms import UserForm, SForm
from watchlist.emails import send_message
from watchlist.schedulers import task_daily

from arxiv.arxiv import arXiv

arx = arXiv(results_per_iteration=5, time_sleep=0.5)


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', form=SForm())


@app.route('/arxiv', methods=['GET', 'POST'])
def arxiv():
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
                    flash('Login firstly.', category="warning")
                    return redirect(url_for('login'))
                else:
                    if db.session.query(arXivEmail).filter_by(
                            email=current_user.email,
                            keyword=str(form_arg['keyword']),
                            author=str(form_arg['author']),
                            subjectcategory=str(form_arg['Subject_Category']
                                                )).first() is not None:
                        flash(u'该监控配置已存在', category="danger")
                        return redirect(url_for('index'))
                    arxivemail = arXivEmail(email=current_user.email,
                                            keyword=str(form_arg['keyword']),
                                            author=str(form_arg['author']),
                                            subjectcategory=str(
                                                form_arg['Subject_Category']),
                                            period=form_arg['period'])

                    arxivemail.lastTracktime = datetime.datetime.now(
                    ) - datetime.timedelta(days=form_arg['period'])
                    db.session.add(arxivemail)
                    db.session.commit()
                    Thread(target=task_daily).start()
                    flash(u'监控添加成功', category="success")
                    return redirect(url_for('index'))
            else:
                flash('Form verification failed.', category="danger")
                return render_template('index.html', form=form)
        except Exception:
            logger.exception('Faild.')
            flash('Get a Exception.', category="danger")
            return render_template('index.html', form=form)
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':  # 判断是否是 POST 请求
        try:
            form = UserForm(formdata=request.form)
            if not form.validate():
                flash('Invalid input!', category="danger")
                return render_template('register.html', form=form)

            email = form.email.data
            captcha = form.captcha.data
            password = form.password.data
            password_valid = form.password_valid.data

            mc_captcha = mc.get(email)
            logger.info(mc_captcha)
            if mc_captcha is None:
                flash(
                    u'Wrong captcha or captcha has been expired, please resend!',
                    category="danger")
                return render_template('register.html', form=form)
            elif mc_captcha != captcha:
                flash(u'Wrong captcha!', category="danger")
                return render_template('register.html', form=form)

            if not (len(email) <= 50 and 8 <= len(password) <= 20):
                flash('Invalid input length!', category="warning")
                return render_template('register.html', form=form)

            if password != password_valid:
                flash('Password is inconsistent!', category="danger")
                return render_template('register.html', form=form)

            user = User.query.get(email)
            if user is not None:
                flash('Email exists.', category="danger")
                return render_template('register.html', form=form)

            user = User(email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            flash('Register success.', category="success")
            return redirect(url_for('index'))

        except Exception:
            logger.exception('Faild to Register.')
            flash('Get a Exception.', category="danger")

    return render_template('register.html', form=UserForm())


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':  # 判断是否是 POST 请求
        try:
            form = UserForm(formdata=request.form)
            if not form.validate():
                flash('Invalid input!', category="danger")
                return render_template('login.html', form=form)

            email = form.email.data
            password = form.password.data

            if not (len(email) <= 50 and 8 <= len(password) <= 20):
                flash('Invalid input!', category="danger")
                return redirect(url_for('login'))

            user = User.query.get(email)
            if user is None or not user.validate_password(password):
                flash('User does not exist or password is wrong.',
                      category="warning")
                return redirect(url_for('login'))

            login_user(user)
            flash('Login success.', category="success")
            return redirect(url_for('index'))

        except Exception:
            logger.exception('Faild to Login.')
            flash('Get a Exception.', category="danger")

    return render_template('login.html', form=UserForm())


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout success.', category="success")
    return redirect(url_for('index'))


@app.route('/delete/<int:arxiv_id>', methods=['POST'])
@login_required
def delete(arxiv_id):
    if current_user.email == os.environ.get('EMAIL'):
        arxivemail = db.session.query(arXivEmail).filter_by(
            id=arxiv_id).first()
    else:
        arxivemail = db.session.query(arXivEmail).filter_by(
            email=current_user.email, id=arxiv_id).first()
        if arxivemail is None:
            flash('Deleted failed.', category="warning")
            return redirect(url_for('states'))
    db.session.delete(arxivemail)
    db.session.commit()
    flash('Item deleted.', category="success")
    return redirect(url_for('states'))


@app.route('/logoff', methods=['POST'])
@login_required
def logoff():
    arxivemails = db.session.query(arXivEmail).filter_by(
        email=current_user.email).all()
    for arxivemail in arxivemails:
        db.session.delete(arxivemail)
    user = db.session.query(User).get(current_user.email)
    logout_user()
    db.session.delete(user)
    db.session.commit()
    flash('logoff success.', category="success")
    return redirect(url_for('index'))


@app.route('/states')
@login_required
def states():
    if current_user.email == os.environ.get('EMAIL1'):
        users = db.session.query(User).all()
        arxivemails = db.session.query(arXivEmail).all()
    else:
        users = 0
        arxivemails = db.session.query(arXivEmail).filter_by(
            email=current_user.email).all()
    return render_template('states.html', users=users, arxivemails=arxivemails)


@app.route('/email_captcha', methods=['GET'])
def email_captcha():
    email = request.args.get('email')
    if not email:
        return jsonify({"error": 1001, "msg": "Email地址有误"})

    source = list(string.ascii_letters + string.digits)
    # 随机抽取六个字符
    captcha = random.sample(source, 6)
    captcha = "".join([k for k in captcha])

    try:
        send_message(to=email,
                     subject="paper tracker captcha",
                     sender=("yuri", app.config['MAIL_USERNAME']),
                     template="captcha",
                     captcha=captcha)
        mc.set(key=email, val=captcha, time=60 * 5, min_compress_len=6)
    except Exception:
        return jsonify({"error": 1001, "msg": "验证码发送失败"})
    return jsonify({"success": 200, "msg": "验证码发送成功"})


@app.route('/about')
def about():
    return render_template('about.html')
