#!/bin/bash
cd /opt/wbproducts
pkill -9 -f "python.*main.py"
sleep 2
nohup /opt/wbproducts/venv/bin/python /opt/wbproducts/main.py > /opt/wbproducts/bot.log 2>&1 &
sleep 2
ps aux | grep "python.*main.py" | grep -v grep
echo "Bot restarted successfully"
