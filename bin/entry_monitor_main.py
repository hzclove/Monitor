#!/usr/bin/python
# -*- coding: gb18030 -*-


import os
import sys
import Queue
import machine_monitor
import process_monitor
import detector_monitor
import warn_output


if __name__ == "__main__":
    #多线程共享的消息队列
    warn_queue = Queue.Queue()
    #服务器机器监控线程
    machine_monitor_thread = machine_monitor.MachineMonitorThread(warn_queue)
    machine_monitor_thread.start()
    print 'start machine_monitor_thread'
    #后台服务进程监控线程
    process_monitor_thread = process_monitor.ProcessMonitorThread(warn_queue)
    process_monitor_thread.start()
    print 'start process_monitor_thread'
    #http探测监控线程
    detector_monitor_thread = detector_monitor.DetectorMonitorThread(warn_queue)
    detector_monitor_thread.start()
    print 'start detector_monitor_thread'
    #消息发送线程
    warn_output_thread = warn_output.WarnOutputThread(warn_queue)
    warn_output_thread.start()
    print 'start warn_output_thread'
    machine_monitor_thread.join()
    process_monitor_thread.join()
    detector_monitor_thread.join()
    warn_output_thread.join()
    
