#!/usr/bin/python
# coding:utf-8
import sys
import urllib2
import time
import json
import threading
import os
import smtplib    
from email.MIMEText import MIMEText    
from email.header import Header

reload(sys)
sys.setdefaultencoding('utf-8')

#接收人的企业邮箱
receiver_confs = {
    'lulei': 'lulei@withustudy.com',
    'caiboke': 'caiboke@withustudy.com',
    'pengzhao': 'pengzhao@withustudy.com',
    'liusong': 'liusong@withustudy.com',
    'louyongfeng': 'louyongfeng@withustudy.com',
    'huangzhongcheng': 'huangzhongcheng@withustudy.com',
}

class Token(object):
    # 获取token,调用微信企业公众号提供的接口获取
    def __init__(self, corpid, corpsecret):
        self.baseurl = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={0}&corpsecret={1}'.format(corpid, corpsecret)
        self.expire_time = sys.maxint

    def get_token(self):
        if self.expire_time > time.time():
            request = urllib2.Request(self.baseurl)
            response = urllib2.urlopen(request)
            ret = response.read().strip()
            ret = json.loads(ret)
            if 'errcode' in ret.keys():
                print '获取微信接口token失败，%s' % (ret['errmsg'])
                print >> ret['errmsg'], sys.stderr #将错误信息写入到sys日志中
                sys.exit(1)
            self.expire_time = time.time() + ret['expires_in']
            self.access_token = ret['access_token']
        return self.access_token


#发送邮件，将错误信息以邮件类型发送
class SendEmail(object):
    def __init__(self, ip, msg, owner, address):
        self.__ip__ = ip
        self.__msg__ = msg
        self.__owner__ = owner
        self.__address__ = address.split('|')

    def send(self):
        msg = MIMEText('【口袋告警】机器IP%s \n 异常内容%s \n 处理人%s' % (self.__ip__, self.__msg__, self.__owner__),'plain','utf-8')
        msg['Subject'] = Header('口袋学习后台告警', 'utf-8')
        try:
            s=smtplib.SMTP()
            s.connect('smtp.qiye.163.com',25)
            s.login('huangzhongcheng@withustudy.com','564335wkx')
            for address in self.__address__:
                s.sendmail('huangzhongcheng@withustudy.com',receiver_confs[address],msg.as_string())
            s.close()
        except Exception, e:
            print '发送邮件失败，Exception：%s' % (e)
        return 

#发送微信，将后台报警信息以微信形式发送到指定负责人
class SendWeiXin(object):
    def __init__(self, ip, msg, owner, duty):
        self.__ip__ = ip
        self.__msg__ = msg
        self.__owner__ = owner
        self.__duties__ = duty
    def send(self):
        corpid = "wx73f88bc028f156a6"  # 填写微信企业公众号自己应用的，当更改应用corpid随之改变
        corpsecret = "nm1k4MuUY7H_-tVtqW6EWkFFh-tZe8zn7qoDrtM6PERI0ZpCATw9P1NYemKdY0Nl" # 填写微信企业公众号自己应用的，改变应用则corpsecret改变
        qs_token = Token(corpid=corpid, corpsecret=corpsecret).get_token()
        url = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={0}".format(qs_token)
        payload = {
            "touser": "{0}".format(self.__duties__),
            "msgtype": "text",
            "agentid": "1",
            "text": {
                "content": "【口袋告警】机器IP{0}\n 异常内容{1}\n 处理人{2}".format(self.__ip__, self.__msg__, self.__owner__)

            },
            "safe": "0"
        }
        request = urllib2.Request(url)
        request.add_header('Content-Type', 'application/json')
        try:
            response = urllib2.urlopen(request, json.dumps(payload, ensure_ascii=False)).read()
        except urllib2.URLError, e:
            print '发送微信企业号消息失败,urllib2.URLError: %s' % (e.reason)
        return


#错误格式定义
class WarnInfo:
    def __init__(self, ip, msg, owner):
        self.ip = ':'+ip
        timestamp = time.strftime('%m-%d %H:%M:%S',time.localtime(time.time()))
        self.msg = ':%s [%s]' %(msg, timestamp)
        self.receivers = owner
        self.owner = ':' + self.receivers.split('|')[0]


class WarnOutputThread(threading.Thread):
    def __init__(self, warn_queue, interval=1):
        threading.Thread.__init__(self)
        self.__queue__ = warn_queue
        self.__interval__ = interval
    #线程运行
    def run(self):
        while True:
            warn_info = self.__queue__.get()
            SendEmail(ip=warn_info.ip, msg=warn_info.msg, owner=warn_info.owner, address=warn_info.receivers).send()
            SendWeiXin(ip=warn_info.ip, msg=warn_info.msg, owner=warn_info.owner, duty=warn_info.receivers).send()
            time.sleep(self.__interval__)
