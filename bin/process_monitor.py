#!/usr/bin/python
# -*- coding: utf8 -*-

import os
import threading
import time
from warn_output import WarnInfo

'''检查进程是否存在'''

#服务器监控配置
process_confs = [
    ['jetty-distribution2', '101.200.200.130;101.200.201.201', 'huangzhongcheng|caiboke|lulei'], #图片服务器
    ['exercise_server', '101.200.199.209;123.57.231.143', 'pengzhao|caiboke|lulei'], #刷题
    ['broker.as.AppMain', '101.200.199.209;123.57.231.143', 'liusong|louyongfeng|caiboke|lulei|pengzhao'], #broker
    ['NewsServerMain', '101.200.199.209;123.57.231.143', 'huangzhongcheng|caiboke|lulei'], #资讯
    ['AccountServerMain', '101.200.199.209;123.57.231.143', 'liusong|louyongfeng|caiboke|lulei'], #账号
    ['entry_bbs_main', '123.57.228.80;123.57.231.185', 'huangzhongcheng|lulei|caiboke'], #社区
    ['entry_share_main', '123.57.228.80;123.57.231.185', 'huangzhongcheng|lulei|caiboke'], #分享
]

#后台进程监控信息
class ProcessInfo:
    #进程信息
    def __init__(self, proc_name, proc_ips, owner):
        self.__proc_name__ = proc_name.strip()
        self.__owner__ = owner
        self.__except_msgs__ = set()
        for proc_ip in proc_ips.strip().split(';'):
            if os.system('ssh %s "ps aux | grep -v grep | grep %s" > /dev/null 2>&1' %(proc_ip, self.__proc_name__)) != 0:
                self.__except_msgs__.add('%s %s not exist' %(proc_ip, self.__proc_name__))
            #对broker进程所在机器监控连接句柄数
            if proc_name == 'broker.as.AppMain':
                conn_info = os.popen('ssh %s "netstat -n"' %(proc_ip)).read().strip().split('\n')
                conn_list = [v.strip().split()[-1] for v in conn_info if v.startswith('tcp')]
                total_conn_num = len(conn_list)
                close_wait_num = conn_list.count('CLOSE_WAIT')
                time_wait_num = conn_list.count('TIME_WAIT')
                if close_wait_num > 2000 or time_wait_num > 2000 or total_conn_num > 15000:
                    connection_infos = '|'.join(['%s=%d' %(v, conn_list.count(v)) for v in set(conn_list)])
                    self.__except_msgs__.add('%s connections: %s' %(proc_ip, connection_infos))

    #获取服务器异常信息
    def assemble_warn_info(self):
        if self.__except_msgs__:
            warn_msg = ';'.join(self.__except_msgs__)
            return WarnInfo(self.__proc_name__, warn_msg, self.__owner__)


class ProcessMonitorThread(threading.Thread):
    def __init__(self, warn_queue, interval=30):
        threading.Thread.__init__(self)
        self.__queue__ = warn_queue
        self.__interval__ = interval #监控周期
    #线程运行
    def run(self):
        global process_confs
        while True:
            time.sleep(self.__interval__)
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
            print '[%s] update process monitor thread' %(timestamp)
            for proc_name, proc_ips, owner in process_confs:
                process_info = ProcessInfo(proc_name, proc_ips, owner)
                warn_info = process_info.assemble_warn_info()
                if not warn_info:
                    continue
                self.__queue__.put(warn_info)
