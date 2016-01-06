#!/usr/bin/python
# -*- coding: utf8 -*-

'''通过http探测查看服务是否正常'''

import os
import threading
import time
import urllib2
import json
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
from warn_output import WarnInfo


#探测请求监控配置
detector_confs = [
    #刷题监控: 1.请求专业
    ['http://m.kdzikao.com/exercise/select_major', \
        'uid=65d67a31eff9e68bf2cae601ab89af26', \
        'get', lambda res : ('provMajors' in res) and (len(res['provMajors']) >= 14), \
        'pengzhao|caiboke|lulei'],
    #刷题监控: 2.获取科目摘要信息
    ['http://m.kdzikao.com/exercise/subject_summary', \
        {"uid": "65d67a31eff9e68bf2cae601ab89af26", "subjectId": "0_01C1503_00633"}, \
        'post', lambda res : ('subjectState' in res), \
        'pengzhao|caiboke|lulei'],
    #刷题监控: 6.
    ['http://m.kdzikao.com/exercise/sequence_summary', \
        {"uid": "65d67a31eff9e68bf2cae601ab89af26", "subjectId": "0_01C1503_00633"}, \
        'post', lambda res : ('chapterSummary' in res), \
        'pengzhao|caiboke|lulei'],
    #刷题监控: 7.顺序刷题
    ['http://m.kdzikao.com/exercise/do_sequence_exercise', \
        {"userSubject": {"uid": "65d67a31eff9e68bf2cae601ab89af26", "subjectId": "0_01C1503_00633"}, "beginSection": {"id": "04-150701-09_1.1", "name": "c", "sn": "b"}}, \
        'post', lambda res : ('exercises' in res), \
        'pengzhao|caiboke|lulei'],
    #刷题监控: 8.智能刷题
    ['http://m.kdzikao.com/exercise/do_smart_exercise', \
        {"userSubject": {"uid": "65d67a31eff9e68bf2cae601ab89af26", "subjectId": "0_01C1503_00633"}}, \
        'post', lambda res : ('exercises' in res), \
        'pengzhao|caiboke|lulei'],
    #刷题监控: 9.刷题排行
    ['http://m.kdzikao.com/exercise/brush_rank', \
        {"userSubject": {"uid": "65d67a31eff9e68bf2cae601ab89af26", "subjectId": "0_01C1503_00633"}, "timeSpan": "BRUSH_RANK_TIME_SPAN_TODAY"}, \
        'post', lambda res : ('myRankPos' in res), \
        'pengzhao|caiboke|lulei'],
    #刷题监控: 13.模考
    ['http://m.kdzikao.com/exercise/start_mock_exam', \
        {"userSubject": {"uid": "65d67a31eff9e68bf2cae601ab89af26", "subjectId": "0_01C1503_00633"}, "level": "HIGH"}, \
        'post', lambda res : ('exerciseId' in res), \
        'pengzhao|caiboke|lulei'],
    #刷题监控: 14.redis访问
    ['http://m.kdzikao.com/exercise/get_major_subject', \
        'uid=65d67a31eff9e68bf2cae601ab89af26', \
        'get', lambda res : ('major' in res) and ('majorId' in res['major']) and (res['major']['majorId']), \
        'pengzhao|caiboke|lulei'],
    #社区热帖
    ['http://bbs.kdzikao.com/hottestTopicApi/list/bbs.page', \
        'userid=0b3d30a091d120b73b78011824dc159f', \
        'get', lambda res : (res['result'] == 'true'), \
        'huangzhongcheng|lulei|caiboke'],
    #资讯GetBasicNews
    ['http://m.kdzikao.com/news/get_basic_news', \
        'provinceId=1&majorId=1_020204&lastIndex=0&newsType=EXAMINATION_ROAD&imei=0', \
        'get', lambda res : True, \
        'huangzhongcheng|lulei|caiboke'],
    #账户GetUserBasicNewsInfo
    ['http://m.kdzikao.com/account/get_user_basic_info', \
        'uid=c94bdba6207e58aeab4b14a56a2a556e&imei=1', \
        'get', lambda res : True, \
        'louyongfeng|lulei|caiboke'],
    #账户Login
    ['http://m.kdzikao.com/account/login', \
        {"accountType":"INNER_TYPE","phoneNumber":"18710147265","passWord":"E10ADC3949BA59ABBE56E057F20F883E"}, \
        'post', lambda res : True, \
        'louyongfeng|lulei|caiboke'],
]


#探测器监控信息
class DetectorInfo:
    #探测器信息
    def __init__(self, url, param, type, check_func, owner):
        self.__url__ = url
        self.__param__ = param
        self.__type__ = type
        self.__owner__ = owner
        self.__except_info__ = ''
        try:
            if type == 'get':
                request = urllib2.Request('%s?%s' %(url, param))
                response = urllib2.urlopen(request).read()
            else:
                request = urllib2.Request(url)
                request.add_header('Content-Type', 'application/json')
                response = urllib2.urlopen(request, json.dumps(param)).read()        
            rsp_json = json.loads(response)
            if check_func and not check_func(rsp_json):
                self.__except_info__ = 'check json fail'
        except urllib2.HTTPError, he:
            self.__except_info__ = '%d %s' %(he.code, he.reason)
        except urllib2.URLError, ue:
            self.__except_info__ = ue.reason
        except ValueError, ve:
            self.__except_info__ = ve
    #获取探测器异常信息
    def assemble_warn_info(self):
        if self.__except_info__:
            return WarnInfo(self.__url__, self.__except_info__, self.__owner__)


class DetectorMonitorThread(threading.Thread):
    def __init__(self, warn_queue, interval=30):
        threading.Thread.__init__(self)
        self.__queue__ = warn_queue
        self.__interval__ = interval #监控周期
    #线程运行
    def run(self):
        global detector_confs
        while True:
            time.sleep(self.__interval__)
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
            print '[%s] update detector monitor thread' %(timestamp)
            for url, param, type, check_func, owner in detector_confs:
                detector_info = DetectorInfo(url, param, type, check_func, owner)
                warn_info = detector_info.assemble_warn_info()
                if not warn_info:
                    continue
                self.__queue__.put(warn_info)
