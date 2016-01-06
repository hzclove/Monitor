#!/usr/bin/python
# -*- coding: utf8 -*-

import os
import threading
import time
from warn_output import WarnInfo

'''监控服务器机器的disk/memory指标'''

#服务器监控配置
machine_confs = [
    ['123.57.228.80', 'huangzhongcheng|lulei|caiboke'], #社区/分享
    ['123.57.231.185', 'huangzhongcheng|lulei|caiboke'], #社区/分享
    ['101.200.199.209', 'pengzhao|caiboke|lulei|liusong|louyongfeng|huangzhongcheng'], #刷题/broker/资讯/账号
    ['123.57.231.143', 'pengzhao|caiboke|lulei|liusong|louyongfeng|huangzhongcheng'], #刷题/broker/资讯/账号
    ['101.200.200.130', 'huangzhongcheng|lulei|caiboke'], #图片服务器
    ['101.200.201.201', 'huangzhongcheng|lulei|caiboke'], #图片服务器
]

memory_use_warn = 90 #内存
disk_use_warn = 95  #磁盘

#服务器机器监控信息
class MachineInfo:
    #定义内存信息
    class MemoryInfo:
        def __init__(self):
            self.total_size = '' #内存总大小
            self.use_percent = 0 #内存使用率
        def assemble_warn_message(self):
            global memory_use_warn
            if self.use_percent >= memory_use_warn:
                return 'mem used[%d%%], ' %(self.use_percent)
            return ''
    #定义磁盘信息
    class DiskInfo:
        def __init__(self):
            self.mount_path = '' #磁盘挂载路径
            self.total_size = '' #磁盘总大小
            self.use_percent = 0 #磁盘使用率
        def assemble_warn_message(self):
            global disk_use_warn
            if self.use_percent >= disk_use_warn:
                return 'disk[%s] used[%d%%], ' %(self.mount_path, self.use_percent)
            return ''
    #服务器信息
    def __init__(self, ip, owner):
        self.__ip__ = ip
        self.__owner__ = owner
        self.__memory__ = MachineInfo.MemoryInfo()
        self.__fetch_memory_info__()
        self.__disks__ = []
        self.__fetch_disk_infos__()
    #获取服务器内存信息
    def __fetch_memory_info__(self):
        self.memory_detail = os.popen('ssh %s "cat /proc/meminfo"' %(self.__ip__)).read().strip()
        MemTotal, MemAvailable = '', ''
        for item in self.memory_detail.split('\n'):
            item = item.strip()
            if item.startswith('MemTotal:'):
                MemTotal = ' '.join(item.split()[1:])
            if item.startswith('MemAvailable:'):
                MemAvailable = ' '.join(item.split()[1:])
        self.__memory__.total_size = ''.join(MemTotal.split())
        self.__memory__.use_percent = 100 - int(MemAvailable.split()[0])*100/int(MemTotal.split()[0])
    #获取服务器磁盘信息
    def __fetch_disk_infos__(self):
        self.disks_detail = os.popen('ssh %s "df -lh"' %(self.__ip__)).read().strip()
        for item in self.disks_detail.split('\n'):
            if item.find('dev') < 0 or item.find('tmpfs') >= 0:
                continue
            fstype, total, used, avail, percent, mount_path = item.strip().split()
            disk_info = MachineInfo.DiskInfo()
            disk_info.mount_path = mount_path
            disk_info.total_size = total
            disk_info.use_percent = int(percent[:-1])
            self.__disks__.append(disk_info)
    #获取服务器异常信息
    def assemble_warn_info(self):
        machine_warn_msg = ''
        machine_warn_msg += self.__memory__.assemble_warn_message()
        for disk in self.__disks__:
            machine_warn_msg += disk.assemble_warn_message()
        if machine_warn_msg:
            return WarnInfo(self.__ip__, machine_warn_msg, self.__owner__)


class MachineMonitorThread(threading.Thread):
    def __init__(self, warn_queue, interval=30):
        threading.Thread.__init__(self)
        self.__queue__ = warn_queue
        self.__interval__ = interval #监控周期
    #线程运行
    def run(self):
        global machine_confs
        while True:
            time.sleep(self.__interval__)
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
            print '[%s] update machine monitor thread' %(timestamp)
            for ip, owner in machine_confs:
                machine_info = MachineInfo(ip, owner)
                warn_info = machine_info.assemble_warn_info()
                if not warn_info:
                    continue
                self.__queue__.put(warn_info)            
