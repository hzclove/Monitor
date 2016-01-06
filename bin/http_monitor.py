#!/usr/bin/python
# -*- coding: utf8 -*-

import os
import threading
import time
import warn_output

'''检查HTTP探测请求响应是否正常'''

#服务器监控配置
process_confs = [
    ['', ],
]

#探测信息
class DetectInfo:
    #进程信息
    def __init__(self, proc_name, proc_ips, owner):
        self.__proc_name__ = process_name.strip()
        self.__owner__ = owner
        self.__except_ips__ = set()
        for proc_ip in proc_ips.strip().split(';'):
            if os.system('ssh %s "ps aux | grep -v grep | grep %s"' %(proc_ip, self.__proc_name__)) != 0:
                self.__except_ips__.add(proc_ip)
    #获取服务器异常信息
    def assemble_warn_info(self):
        if self.__except_ips__:
            warn_ip = '/'.join(self.__except_ips__)
            warn_msg = '%s not exist' %(self.__proc_name__)
            return WarnInfo(warn_ip, warn_msg, self.__owner__)


class DetectMonitorThread(threading.Thread):
    def __init__(self, warn_queue, interval=5):
        threading.Thread.__init__(self)
        self.__queue__ = warn_queue
        self.__interval__ = interval #监控周期
    #线程运行
    def run(self):
        global process_confs
        while True:
            for proc_name, proc_ips, owner in process_confs:
                process_info = ProcessInfo(proc_name, proc_ips, owner)
                warn_info = process_info.assemble_warn_info()
                if not warn_info:
                    continue
                self.__queue__.put(warn_info)
            time.sleep(self.__interval__)
