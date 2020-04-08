#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from arxiv.arxiv import arXiv

from flask import Flask
from flask import request, render_template
from flask import url_for, redirect, flash

from flask_mail import Mail, Message
from flask_login import LoginManager, UserMixin, current_user
from flask_login import login_user, logout_user, login_required

from wtforms import Form
from wtforms import IntegerField, StringField, SelectMultipleField, RadioField, widgets
from wtforms.validators import InputRequired, NumberRange, Length, Email

import os
import sys
import click
from pathlib import Path
import datetime

from flask_sqlalchemy import SQLAlchemy

logging.basicConfig(format='%(asctime)s - %(filename)s[line:%(lineno)d] - '
                    '%(levelname)s: %(message)s',
                    level=logging.INFO,
                    filename="log.log",
                    filemode="w+")
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
    app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控

mail = Mail(app)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

arx = arXiv(db_path=str(Path.cwd() / 'db'),
            results_per_iteration=5,
            time_sleep=0.5)


@app.cli.command()  # 注册为命令
@click.option('--drop', is_flag=True, help='Create after drop.')
# 设置选项
def initdb(drop):
    """Initialize the database."""
    if drop:  # 判断是否输入了选项
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')  # 输出提示信息


@login_manager.user_loader
def load_user(user_email):
    user = User.query.get(user_email)
    return user


class User(db.Model, UserMixin):  # 表名将会是 user（自动生成，小写处理）
    # id = db.Column(db.Integer, autoincrement=True, unique=True)
    email = db.Column(db.String(50), primary_key=True)  # 邮箱, 主键
    username = db.Column(db.String(20))  # 用户名

    def get_id(self):
        return self.email


class arXivEmail(db.Model):  # 表名将会是 email（自动生成，小写处理）
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 主键
    email = db.Column(db.String(50), db.ForeignKey('user.email'))  # 邮箱, 设置外键
    lastTracktime = db.Column(db.DateTime,
                              default=datetime.datetime.now,
                              nullable=False)
    keyword = db.Column(db.Text())  # 关键字
    author = db.Column(db.Text())  # 作者
    subjectcategory = db.Column(db.Text(), nullable=False)  # 主题
    period = db.Column(db.Integer(), nullable=False)  # 检测时段


class LoginForm(Form):
    username = StringField(u'用户名(长度4-20)：',
                           validators=[
                               InputRequired(message=u'用户名不能为空!'),
                               Length(min=4, max=20, message=u'用户名长度为4-20')
                           ])
    email = StringField(u'Email地址(长度<50)：',
                        validators=[
                            Email(message=u'Email地址不合法!'),
                            InputRequired(message=u'Email地址不能为空!'),
                            Length(max=50, message=u'Email地址长度需小于50')
                        ])

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)


class SForm(Form):
    sc_list = [
        ('cs.AI', 'Artificial Intelligence'),
        ('cs.CC', 'Computational Complexity'),
        ('cs.CG', 'Computational Geometry'),
        ('cs.CE', 'Computational Engineering, Finance, and Science'),
        ('cs.CL',
         'Computation and Language (Computational Linguistics and Natural Language and Speech Processing)'
         ), ('cs.CV', 'Computer Vision and Pattern Recognition'),
        ('cs.CY', 'Computers and Society'),
        ('cs.CR', 'Cryptography and Security'), ('cs.DB', 'Databases'),
        ('cs.DS', 'Data Structures and Algorithms'),
        ('cs.DL', 'Digital Libraries'), ('cs.DM', 'Discrete Mathematics'),
        ('cs.DC', 'Distributed, Parallel, and Cluster Computing'),
        ('cs.ET', 'Emerging Technologies'),
        ('cs.FL', 'Formal Languages and Automata Theory'),
        ('cs.GT', 'Computer Science and Game Theory'),
        ('cs.GL', 'General Literature'), ('cs.GR', 'Graphics'),
        ('cs.AR', 'Hardware Architecture'),
        ('cs.HC', 'Human-Computer Interaction'),
        ('cs.IR', 'Information Retrieval'), ('cs.IT', 'Information Theory'),
        ('cs.ML', 'Machine Learning'), ('cs.LO', 'Logic in Computer Science'),
        ('cs.MS', 'Mathematical Software'), ('cs.MA', 'Multiagent Systems'),
        ('cs.MM', 'Multimedia'),
        ('cs.NI', 'Networking and Internet Architecture'),
        ('cs.NE', 'Neural and Evolutionary Computation'),
        ('cs.NA', 'Numerical Analysis'), ('cs.OS', 'Operating Systems'),
        ('cs.PF', 'Performance'), ('cs.PL', 'Programming Languages'),
        ('cs.RO', 'Robotics'), ('cs.SI', 'Social and Information Networks'),
        ('cs.SE', 'Software Engineering'), ('cs.SD', 'Sound'),
        ('cs.SC', 'Symbolic Computation'), ('cs.SY', 'Systems and Control'),
        ('cs.OH', 'Other')
    ]
    keyword = StringField(u'关键词(多个关键词之间使用 空格 分隔,可为空)：')
    author = StringField(u'作者(多个作者之间使用 逗号(,) 分隔,可为空)：')
    period = IntegerField(u'监测时间间隔(0-31)：',
                          validators=[
                              InputRequired(message=u'取值范围为0-31天!'),
                              NumberRange(1, 31, message=u'取值为0-31天!')
                          ])
    func = RadioField(label=u"功能(监测需要先登陆)：",
                      choices=(
                          (0, "预览查询最多5篇论文"),
                          (1, "监测"),
                      ),
                      coerce=int,
                      default=0)
    subjectCategory = SelectMultipleField(
        u'主题(默认已选择部分与安全的主题)：',
        choices=sorted(sc_list, key=lambda x: len(x[1])),
        default=["cs.AI", "cs.CR", "cs.SE", "cs.CY", "cs.SE", "cs.CE"],
        validators=[InputRequired(message=u'请至少选择一个主题!')],
        option_widget=widgets.CheckboxInput(),
        widget=widgets.ListWidget(prefix_label=False))

    def __init__(self, *args, **kwargs):
        super(SForm, self).__init__(*args, **kwargs)

    def get_arg(self):
        kw = self.keyword.data  # 关键词
        au = self.author.data  # 作者
        sc = self.subjectCategory.data  # 主题
        fc = int(self.func.data)
        sp = int(self.period.data)  # 时期
        if ' ' in kw:
            kw = kw.split(' ')
        if ',' in au:
            au = au.split(',')
        arg_dict = {
            'keyword':
            kw,
            'author':
            au,
            'Subject_Category':
            sc,
            'Subject_Category_name':
            [sc_[1] for k in sc for sc_ in self.sc_list if k == sc_[0]],
            'period':
            sp,
            'function':
            fc
        }
        return arg_dict


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

                if fc == 1 and not current_user.is_authenticated:
                    flash('Login firstly.')
                    return redirect(url_for('login'))

                if fc == 0:
                    result_dict, num = arx.search(**form_arg, max_ind=5)
                    return render_template('arxiv.html',
                                           result_dict=result_dict,
                                           num=num,
                                           form_arg=form_arg,
                                           SC_name=SC_name)
                else:
                    msg = Message(
                        'paper tracker {0}'.format(datetime.date.today()),
                        sender='yuri<{0}>'.format(app.config['MAIL_USERNAME']),
                        recipients=[current_user.email])
                    result_dict, num = arx.search(**form_arg)
                    msg.html = render_template('email.html',
                                               result_dict=result_dict,
                                               num=num,
                                               form_arg=form_arg,
                                               SC_name=SC_name,
                                               time=str(datetime.date.today()))
                    with app.app_context():
                        mail.send(msg)
                    flash('邮件发送成功')
                    return redirect(url_for('index'))
            else:
                flash('Form verification failed.')
                return render_template('index.html', form=form)
        except Exception:
            logger.exception('Faild.')
            flash('Get a Exception.')

    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':  # 判断是否是 POST 请求
        try:
            form = LoginForm(formdata=request.form)
            if not form.validate():
                flash('Invalid input!')
                return render_template('login.html', form=form)

            username = form.username.data
            email = form.email.data
            if len(username) > 20 or len(email) > 50:
                flash('Invalid input!')
                return redirect(url_for('login'))
            user = User.query.get(email)
            if user is None:
                user = User(email=email, username=username)
                db.session.add(user)
                db.session.commit()
            login_user(user)
            flash('Login success.')
            return redirect(url_for('index'))

        except Exception:
            logger.exception('Faild to Login.')
            flash('Get a Exception.')

    return render_template('login.html', form=LoginForm())


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout success.')
    return redirect(url_for('index'))


@app.route('/sendEmail')
@login_required
def send_email():
    msg = Message('paper tracker {0}'.format(datetime.date.today()),
                  sender='yuri<{0}>'.format(app.config['MAIL_USERNAME']),
                  recipients=[current_user.email])
    msg.body = 'hello'
    msg.html = 'html'
    with app.app_context():
        mail.send(msg)
    flash('邮件发送成功')
    return redirect(url_for('index'))
