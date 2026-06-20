"""
Flask 主应用 - 个人题库与试卷管理系统
"""
from flask import Flask, request, jsonify, render_template, send_file, g, abort
import os
import json
import uuid
import shutil
from datetime import datetime, timedelta
from PIL import Image
import io
import re

from . import models
from .models import db, query_all, query_one, execute, now_str

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)


def create_app():
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB
    app.config['UPLOAD_DIR'] = UPLOAD_DIR

    models.init_db()

    # 注册蓝图路由
    from .routes_main import register_routes
    register_routes(app)

    return app
