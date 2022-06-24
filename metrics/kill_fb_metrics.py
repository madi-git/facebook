import signal, psutil
import subprocess
import pymysql
# !/usr/bin/env python
from datetime import datetime, date, timedelta
from stat import S_ISREG, ST_CTIME, ST_MODE
import os, sys, time
#import dateparser

process = ["fb_chrome_metrics.py",
           "Xvfb",
           "chromedriver", 
           "chromium"]

for name in process:
    for proc in psutil.process_iter():
        pinfo = proc.as_dict(attrs=['pid', 'name', 'cmdline'])
        if name in str(pinfo['cmdline']):
            try:
                pid = pinfo['pid']
                parent = psutil.Process(pid)
                for child in parent.children(
                        recursive=True):  # or parent.children() for recursive=False
                    child.kill()
                parent.kill()
            except Exception as e:
                print("e", e)
