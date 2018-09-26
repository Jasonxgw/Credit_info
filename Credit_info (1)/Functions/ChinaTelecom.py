import uuid
import requests
from http import cookiejar
import time
import json
import os
from Config.config import *
import logging
import pickle

# 日志基本配置(同时写入到文件和输出到控制台)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')
logger = logging.getLogger()

base = [str(x) for x in range(10)] + [chr(x) for x in range(ord('A'), ord('A') + 6)]


class China_Telecom(object):
    def __init__(self, uname):
        super(China_Telecom, self).__init__()
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Host': 'gd.189.cn',
            'If-Modified-Since': 'Tue, 18 Sep 2018 07:26:40 GMT',
            'If-None-Match': "pv5f7e0d96673b058d302ae0704e06ea9f",
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.26 Safari/537.36 Core/1.63.5702.400 QQBrowser/10.2.1893.400'
        }
        self.uname = uname
        self.session = requests.session()
        self.session.headers = self.headers.copy()
        self.session.cookies = cookiejar.LWPCookieJar('cookies.txt')
        self.nick_name = uuid.uuid4()
        self.info_dict = {}
        self.operator_info = mongo_connect()['operator_info']

    def save_cookie(self, cookies):
        cookies_dict = {}
        for cookie in cookies:
            if 'name' in cookie and 'value' in cookie:
                cookies_dict[cookie['name']] = cookie['value']
        cookie = cookies_dict
        return cookie

    def _load_cookies(self):
        cookies_file = ''
        for name in os.listdir('./cookies'):
            if name.endswith('.cookies'):
                cookies_file = './cookies/{0}'.format(name)
                break
        with open(cookies_file, 'rb') as f:
            local_cookies = pickle.load(f)
        self.session.cookies.update(local_cookies)
        return self.session
    #获取随机验证码
    def get_random_passwd(self):
        headers = {
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding':'gzip, deflate, br',
            'Accept-Language':'zh-CN,zh;q=0.9',
            'Cache-Control':'max-age=0',
            'Connection':'keep-alive',
            'Host':'gd.189.cn',
            'If-Modified-Since':'Tue, 18 Sep 2018 07:26:40 GMT',
            'If-None-Match':"pv5f7e0d96673b058d302ae0704e06ea9f",
            'Upgrade-Insecure-Requests':'1',
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.26 Safari/537.36 Core/1.63.5702.400 QQBrowser/10.2.1893.400'
        }
        url = 'https://gd.189.cn/dwr/exec/newLoginDwr.getPassword.dwr'
        time_now = int(time.time())
        data = {
            'callCount': '1',
            'c0-scriptName': 'newLoginDwr',
            'c0-methodName': 'getPassword',
            'c0-id': '4779_{}'.format(str(time_now * 1000)),
            'c0-param0':'boolean:false',
            'c0-param1':'boolean:false',
            'c0-param2':'string:{}'.format(self.uname),
            'c0-param3':'string: ',
            'c0-param4':'string:2',
            'xml': True
        }
        response =self.session.post(url=url, data=data,  headers=headers, verify=False)

    def get_captcha_code(self):
        #
        # headers = {
        #     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        #     'Accept-Encoding': 'gzip, deflate, br',
        #     'Accept-Language': 'zh-CN,zh;q=0.9',
        #     'Cache-Control': 'max-age=0',
        #     'Connection': 'keep-alive',
        #     'Host': 'gd.189.cn',
        #     'If-Modified-Since': 'Tue, 18 Sep 2018 07:26:40 GMT',
        #     'If-None-Match': "pv5f7e0d96673b058d302ae0704e06ea9f",
        #     'Upgrade-Insecure-Requests': '1',
        #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.26 Safari/537.36 Core/1.63.5702.400 QQBrowser/10.2.1893.400'
        # }


        url = 'https://gd.189.cn/nCheckCode?kkadf={}'.format(str(random.random()))

        response = self.session.get(url=url, headers=self.session.headers, verify=False)
        captcha_path =  os.path.join('../Verify/images/China_Telecom',
                                    'China_Telecom' + '-' + str(self.uname) + '-' + str(int(time.time())) + '.jpg')
        # cookie = response.cookies
        save_image(response, captcha_path)
        open_image(captcha_path)
        # self.session.cookies = cookie
        return

    def login_by_sms(self):
        url = 'https://gd.189.cn/dwr/exec/newLoginDwr.goLogin.dwr'
        time_now = int(time.time())
        self.get_captcha_code()
        logger.info('请输入短信验证码： ')
        sms_code = input()
        logger.info('请输入图片验证码： ')
        captcha_code = input()

        data = {
            'callCount': '1',
            'c0-scriptName': 'newLoginDwr',
            'c0-methodName': 'goLogin',
            'c0-id': '4779_{}'.format(str(time_now * 1000)),
            'c0-param0': 'boolean:false',
            'c0-param1': 'boolean:false',
            'c0-param2': 'string:{}'.format(captcha_code),
            'c0-param3': 'string: ',
            'c0-param4': 'string:2000004',
            'c0-param5': 'string:{}'.format(self.uname),
            'c0-param6': 'string:04',
            'c0-param7': 'string:{}'.format(sms_code),
            'c0-param8': 'string: ',
            'c0-param9': 'string:sysType%3DNewLogin',
            'xml': True
        }

        response = self.session.post(url=url, data=data, headers=self.session.headers, verify=False)
        return

    def login_by_passwd(self):
        # headers = {
        #     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        #     'Accept-Encoding': 'gzip, deflate, br',
        #     'Accept-Language': 'zh-CN,zh;q=0.9',
        #     'Cache-Control': 'max-age=0',
        #     'Connection': 'keep-alive',
        #     'Host': 'gd.189.cn',
        #     'If-Modified-Since': 'Tue, 18 Sep 2018 07:26:40 GMT',
        #     'If-None-Match': "pv5f7e0d96673b058d302ae0704e06ea9f",
        #     'Upgrade-Insecure-Requests': '1',
        #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.26 Safari/537.36 Core/1.63.5702.400 QQBrowser/10.2.1893.400'
        # }

        url_login = 'https://gd.189.cn/dwr/exec/newLoginDwr.goLogin.dwr'
        time_now = int(time.time())
        logger.info('请输入服务密码： ')
        passwd = input()
        url = 'https://gd.189.cn/nCheckCode?kkadf={}'.format(str(random.random()))
        response_captcha = self.session.get(url=url, headers=self.session.headers, verify=False)
        captcha_path = os.path.join('../Verify/images/China_Telecom',
                                    'China_Telecom' + '-' + str(self.uname) + '-' + str(int(time.time())) + '.jpg')

        save_image(response_captcha, captcha_path)
        open_image(captcha_path)

        logger.info('请输入图片验证码： ')
        captcha_code = input()

        data = {
            'callCount': 1,
            'c0-scriptName': 'newLoginDwr',
            'c0-methodName': 'goLogin',
            'c0-id': '4779_{}'.format(str(time_now * 1000)),
            'c0-param0': 'boolean:false',
            'c0-param1': 'boolean:false',
            'c0-param2': 'string:'.format(captcha_code),
            'c0-param3': 'string:',
            'c0-param4': 'string:2000004',
            'c0-param5': 'string:{}'.format(str(self.uname)),
            'c0-param6': 'string:00',
            'c0-param7': 'string:{}'.format(str(passwd)),
            'c0-param8': 'string:',
            'c0-param9': 'string:sysType%3DNewLogin',
            'xml': True
        }
        response = self.session.post(url=url_login, data=data, headers=self.session.headers, verify=False)
        print(response.text)
        return

    def get_common_data(self):

        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Host': 'gd.189.cn',
            'Content-Length':'32',
            'Content-Type':'application/x-www-form-urlencoded',
            'Origin':'https://gd.189.cn',
            'Referer':'https://gd.189.cn/service/home/query/xf_ye.html?in_cmpid=khzy-zcdh-fycx-wdxf-yecx2018',
            'X-Requested-With':'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.26 Safari/537.36 Core/1.63.5702.400 QQBrowser/10.2.1893.400'
        }

        data = {
            'a.c': '0',
            'a.u': 'user',
            'a.p': 'pass',
            'a.s': 'ECSS'
        }
        self.session.headers.update({'Refer':'https://gd.189.cn/service/home/query/xf_ye.html?in_cmpid=khzy-zcdh-fycx-wdxf-yecx2018'})
        url = 'https://gd.189.cn/J/J10059.j'
        response = self.session.post(url, headers=headers, data=data, verify=False)
        response.encoding='gb2312'
        print(response.text)


if __name__ == '__main__':
    init = China_Telecom('18127013650')
    # init.get_random_passwd()
    # init.get_captcha_code()
    # init.login_by_sms()
    init.login_by_passwd()
    init.get_common_data()


"""
callCount=1
c0-scriptName=newLoginDwr
c0-methodName=goLogin
c0-id=6245_1536748042460
c0-param0=boolean:false
c0-param1=boolean:false
c0-param2=string:LMDZ
c0-param3=string:
c0-param4=string:2000004
c0-param5=string:18127013650
c0-param6=string:00
c0-param7=string:152913
c0-param8=string:
c0-param9=string:sysType%3DNewLogin
xml=true
"""


"""
{'callCount': '1', 
'c0-scriptName': 'newLoginDwr', 
'c0-methodName': 'goLogin', 
'c0-id': '4779_1536802312000',
'c0-param0': 'boolean:false', 
'c0-param1': 'boolean:false', 
'c0-param2': 'string:Y9LD', 
'c0-param3': 'string:',
'c0-param4': 'string:2000004',
'c0-param5': 'string:18127013650',
'c0-param6': 'string:00',
'c0-param7': 'string:152913',
'c0-param8': 'string:', 
'c0-param9': 'string:sysType%3DNewLogin', 
'xml': True}

"""