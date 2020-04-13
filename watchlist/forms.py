#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from wtforms import Form
from wtforms import IntegerField, StringField, SelectMultipleField, RadioField, PasswordField, widgets
from wtforms.validators import InputRequired, NumberRange, Length, Email, Optional, EqualTo


class UserForm(Form):
    password = PasswordField(u'密码(长度8-20)：',
                             validators=[
                                 InputRequired(message=u'密码不能为空!'),
                                 Length(min=8, max=20, message=u'密码长度为4-20')
                             ])
    password_valid = PasswordField(u'再输入一次密码：',
                                   validators=[
                                       Optional(),
                                       InputRequired(message=u'密码不能为空!'),
                                       Length(min=8,
                                              max=20,
                                              message=u'密码长度为4-20'),
                                       EqualTo('password',
                                               message='Passwords must match.')
                                   ])
    email = StringField(u'Email地址(长度<50)：',
                        validators=[
                            Email(message=u'Email地址不合法!'),
                            InputRequired(message=u'Email地址不能为空!'),
                            Length(max=50, message=u'Email地址长度需小于50')
                        ])

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)


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

    @classmethod
    def get_sc_name(cls, sc):
        return [sc_[1] for k in sc for sc_ in cls.sc_list if k == sc_[0]]

    def get_arg(self):
        kw = self.keyword.data.strip()  # 关键词
        au = self.author.data.strip()  # 作者
        sc = self.subjectCategory.data  # 主题
        fc = int(self.func.data)
        sp = int(self.period.data)  # 时期
        if ' ' in kw:
            kw = re.split(r" +", kw)
        if ',' in au:
            au = re.split(r",+", au)
        arg_dict = {
            'keyword': kw,
            'author': au,
            'Subject_Category': sc,
            'Subject_Category_name': self.get_sc_name(sc),
            'period': sp,
            'function': fc
        }
        return arg_dict
