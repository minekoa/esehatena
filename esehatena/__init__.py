#-*- coding:utf-8 -*-

from flask import Flask

app = Flask(__name__, instance_relative_config=True)
from esehatena.views import *
from esehatena.api   import *
app.config.from_pyfile('config.py')

