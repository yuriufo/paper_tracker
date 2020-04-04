#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from arxiv.arxiv import Arxiv

from flask import Flask
from flask import request, render_template
from wtforms import Form
from wtforms import IntegerField, StringField, SelectMultipleField, widgets
from wtforms.validators import DataRequired, Length, NumberRange

from pathlib import Path

logging.basicConfig(format='%(asctime)s - %(filename)s[line:%(lineno)d] - '
                    '%(levelname)s: %(message)s',
                    level=logging.INFO,
                    filename="log.log",
                    filemode="w")
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='./templates')

cpath = Path.cwd()
dbpath = cpath / 'db'
arx = Arxiv(db_path=str(dbpath), results_per_iteration=5, time_sleep=0.5)


class SForm(Form):
    keyword = StringField(
        u'关键词(多个关键词之间使用空格( )分隔)：',
        validators=[DataRequired(message='关键词不能为空.'),
                    Length(1, 64)])
    author = StringField(u'作者(多个作者之间使用逗号(,)分隔)：', validators=[Length(0, 64)])
    period = IntegerField(u'搜索最近多少天的论文(0-31)：',
                          validators=[
                              DataRequired(message='取值范围为0-31天.'),
                              NumberRange(1, 31, message='取值为0-31天.')
                          ])
    subjectCategory = SelectMultipleField(
        u'主题(默认已选择部分与安全的主题)：',
        validators=[DataRequired(message='至少选择一个主题.')],
        option_widget=widgets.CheckboxInput(),
        widget=widgets.ListWidget(prefix_label=False))

    def __init__(self, *args, **kwargs):
        super(SForm, self).__init__(*args, **kwargs)
        self.subjectCategory.choices = sorted([
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
            ('cs.IR', 'Information Retrieval'),
            ('cs.IT', 'Information Theory'), ('cs.ML', 'Machine Learning'),
            ('cs.LO', 'Logic in Computer Science'),
            ('cs.MS', 'Mathematical Software'),
            ('cs.MA', 'Multiagent Systems'), ('cs.MM', 'Multimedia'),
            ('cs.NI', 'Networking and Internet Architecture'),
            ('cs.NE', 'Neural and Evolutionary Computation'),
            ('cs.NA', 'Numerical Analysis'), ('cs.OS', 'Operating Systems'),
            ('cs.PF', 'Performance'), ('cs.PL', 'Programming Languages'),
            ('cs.RO', 'Robotics'),
            ('cs.SI', 'Social and Information Networks'),
            ('cs.SE', 'Software Engineering'), ('cs.SD', 'Sound'),
            ('cs.SC', 'Symbolic Computation'),
            ('cs.SY', 'Systems and Control'), ('cs.OH', 'Other')
        ],
                                              key=lambda x: len(x[1]))
        self.subjectCategory.data = [
            "cs.AI", "cs.CR", "cs.SE", "cs.CY", "cs.SE", "cs.CE"
        ]


@app.route('/')
@app.route('/index')
def index():
    if request.method == 'GET':
        return render_template('index.html', form=SForm())
    else:
        return 'hello'


@app.route('/arxiv', methods=['GET', 'POST'])
def arxiv():
    global arx
    if request.method == 'POST':  # 判断是否是 POST 请求
        form = SForm(formdata=request.form)
        if form.validate():
            try:
                # source = request.form.get('source')  # 数据来源
                kw = form.keyword.data  # 关键词
                au = form.author.data  # 作者
                sc = form.subjectCategory.data  # 主题
                sp = int(form.period.data)  # 时期
                if ' ' in kw:
                    kw = kw.split(' ')
                if ',' in au:
                    au = au.split(',')
                result_dict, _ = arx.search(Subject_Category=sc,
                                            keyword=kw,
                                            period=sp,
                                            author=au)
                return render_template('arxiv.html', result_dict=result_dict)
            except Exception as e:
                logger.error(e)
        else:
            return render_template('index.html', form=form)
    elif request.method == 'GET':
        return render_template('index.html', form=SForm())


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=7777, debug=True)
