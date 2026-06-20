"""
启动脚本 - 单用户本地/局域网访问
"""
import os
import sys

# 将项目根目录加入 sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from app import create_app

app = create_app()
app.config['SECRET_KEY'] = 'zhejiang-it-exam-private-2024'

if __name__ == '__main__':
    print("=" * 60)
    print("  个人题库与试卷管理系统 V3.0")
    print("  浙江省高中信息技术学科专属版")
    print("=" * 60)
    print("  本地访问: http://127.0.0.1:5000")
    print("  局域网访问: http://<本机IP>:5000")
    print("  数据库: data/exam.db")
    print("  附件目录: app/static/uploads/")
    print("=" * 60)
    # 关闭 debug 模式以避免 reloader fork 导致后台进程被杀
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
