#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

import os
import sys
import threading

import redis
from flask import Flask

from test import test_seh
from etc import config
from init_app import init
from base.session import RedisSessionInterface
import views

project_home = os.path.realpath(__file__)
project_home = os.path.split(project_home)[0]

sys.path.insert(0, os.path.split(project_home)[0])
sys.path.insert(0, project_home)

app = Flask(__name__, static_url_path=config.static_path)
init(app)

# redis session
app.session_interface = RedisSessionInterface(redis.StrictRedis(
    connection_pool=redis.ConnectionPool(
        max_connections=config.redis_max_connections,
        **config.redis_config
    )))

# route setting


for name in views.__all__:
    module = __import__('views.%s' % name, fromlist=[name])
    app.register_blueprint(getattr(module, name), url_prefix=config.app_path)

if __name__ == '__main__':
    os.environ['WSGI_CONFIG_MODULE'] = 'local'
    # TODO:启动redis cms 命令行
    threading.Thread(target=test_seh.start, args=("17:48",)).start()
    app.run(host='127.0.0.1',
            port=config.debug_port)

