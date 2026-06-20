#!/bin/bash
# 持久化启动脚本 - 写一个 PID 文件，使用 double-fork daemonize
PIDFILE=/tmp/exam_flask.pid
LOGFILE=/tmp/flask.log

# 杀掉旧进程
if [ -f "$PIDFILE" ]; then
    OLDPID=$(cat $PIDFILE)
    kill -9 $OLDPID 2>/dev/null
    rm -f $PIDFILE
fi
pkill -f "run.py" 2>/dev/null
sleep 1

cd /home/z/my-project

# Double-fork daemonize
python3 - <<'EOF' &
import os, sys, subprocess
# First fork
pid = os.fork()
if pid > 0:
    sys.exit(0)
os.setsid()
# Second fork
pid = os.fork()
if pid > 0:
    sys.exit(0)
# Redirect stdio
sys.stdout.flush()
sys.stderr.flush()
with open('/dev/null','r') as f: os.dup2(f.fileno(), 0)
with open('/tmp/flask.log','a') as f: 
    os.dup2(f.fileno(), 1)
    os.dup2(f.fileno(), 2)
# Write PID
with open('/tmp/exam_flask.pid','w') as f:
    f.write(str(os.getpid()))
# Exec
os.execv('/home/z/.venv/bin/python3', ['/home/z/.venv/bin/python3', '/home/z/my-project/run.py'])
EOF

sleep 4
echo "PID: $(cat $PIDFILE 2>/dev/null)"
pgrep -af run.py | head -2
ss -tlnp 2>/dev/null | grep :5000
