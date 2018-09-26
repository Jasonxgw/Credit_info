import requests
from Config.config import *
import time
import json
import random
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
import logging
from tools.jd_tools import save_image,open_image
import os
import pickle
from bs4 import BeautifulSoup
from Config.config import mongo_connect
import uuid
import sys

login_url = 'http://www.51jt.com/home/login.jsp'


db = mongo_connect()['credit_info']
collection = db['WY']
# 自定义 headers
HEADERS = {
        'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; .NET CLR 1.1.4322)',
        'Connection': 'Keep-Alive',
        'x-phoneType': 'android',
        'x-YxbCookie': '',
        'x-version': '3.41',
        'x-osVersion': '5.1.1',
        'x-phoneModel': 'SM-G935F',
        'x-imsi': '460002022913807',
       #  'x-channeId': '9999',
       #  'x-HWUserToken': '',
       #  'x-imei': '865163589444330',
       # 'x-simNumber': '17653711350',
        'x-deviceToken': '',
        'x-androidDeviceToken': '',
        'x-guid': '4aa0ca5597cc0852c5b01a6923307cce',
        'x-udid': 'c9835cc0a7fb5b134aff1bba87e5cc09201809140938425f691bbf8ca1bda032ec369559d0a331',
        'x-device': 'SM-G935F',
        # 'x-uniqueId': '2ae8144b5ba5a7a61fe1ac91c6328bc158661ef64d81e0e9',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': 'www.51jt.com',
        'Accept-Encoding': 'gzip',
        'Content-Length': '197'
        }
list_contact = []
# 日志基本配置(同时写入到文件和输出到控制台)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')
logger = logging.getLogger()


class WYJD(object):
    def __init__(self, uname, upasswd):
        super(WYJD, self).__init__()
        self.session = requests.Session()
        self.session.headers = HEADERS
        # cookie存储
        self.page = 0
        self.uname = uname
        self.upasswd = upasswd
        self.captcha_url = 'https://ic.qq.com/pim/captcha.jsp?'
        self.info_dict = {}
        self.debit = mongo_connect()['WYJD']
        self.list_borrow = []
    def get_common_data(self):
        common_data = {}
        url = 'https://www.51jt.com/api.jsp'
        data = {
            "args":["590f2772abb93638473d377958bc22e4513f95d65b64d4cb"],
            "argsclass":["java.lang.String"],
            "methodName":"autoLoginGetUserInfo",
            "proxy":"UserManager"
        }
        response = self.session.post(url=url, data='json=' + json.dumps(data), verify=False, headers=self.session.headers)
        if response.status_code != 200:
            logger.error('登录状态错误, 请重新登陆')
            sys.exit(0)
        else:
            data = json.loads(response.text)
            name = data['realname']
            phone = self.uname
            email = data['email']
            gender = data['gender']
            interest_rate = data['interestRate']
            t_id = data['t_id']
            regis_date = data['regTime']
            current_money = data['totalMoney'] #现金金额
            unique_id = data['uniqueId']
            wait_receive = data['waitReceiveMoney'] #代收金额
            wait_repay = data['waitRepayMoney'] #待还金额
            self.yxb_token = data['yxbToken']
            self.yxb_cookie = data['yxbCookie']
            self.unique_id = data['uniqueId']
            credit_level = data['creditLevelDesc']
            common_data['name'] = name
            common_data['phone'] = phone
            common_data['email'] = email
            common_data['gender'] = gender
            common_data['credit_level'] = credit_level
            common_data['interest_rate'] = interest_rate
            common_data['t_id'] = t_id
            common_data['regis_date'] = regis_date
            common_data['current_money'] = current_money
            common_data['unique_id'] = unique_id
            common_data['wait_receive'] = wait_receive
            common_data['wait_repay'] = wait_repay
            common_data['yxb_token'] = self.yxb_token
            common_data['yxb_cookie'] = self.yxb_cookie
            common_data['unique_id'] = self.unique_id
            self.info_dict['common_data'] = common_data
            return
    def get_paid_data(self):
        unique_id = self.info_dict['common_data']['unique_id']
        yxb_token =  self.info_dict['common_data']['yxb_token']
        yxb_cookie = self.info_dict['common_data']['yxb_cookie']

        self.session.headers.update({ 'x-YxbCookie': yxb_cookie,'x-HWUserToken': yxb_token, 'x-uniqueId': unique_id})
        url = 'https://www.51jt.com/api.jsp'

        for i in range(1, 5):
            data = {"args":[yxb_token,1,4,i],
                    "argsclass":["java.lang.String","java.lang.Integer","java.lang.Integer","java.lang.Integer"],
                    "methodName":"getLoanListData","proxy":"LoanManagerV22"}
            response = self.session.post(url=url, data='json=' + json.dumps(data), verify=False,
                                         headers=self.session.headers)
            if response.status_code !=200:
                continue
            else:
                data = json.loads(response.text)['value']
                pair_data = {}
                for each in data:
                    loan_id = each['loanID']
                    loan_status = each['loanStatus']
                    loaner = each['name']
                    date = each['time']
                    amount = each['money']
                    interest = each['interest']
                    pair_data['loan_id'] = loan_id
                    pair_data['loan_status'] = loan_status
                    pair_data['loaner'] = loaner
                    pair_data['date'] = date
                    pair_data['amount'] = amount
                    pair_data['interest'] = interest
                    self.list_borrow.append(pair_data)

    def get_overdue(self):
        unique_id = self.info_dict['common_data']['unique_id']
        yxb_token = self.info_dict['common_data']['yxb_token']
        yxb_cookie = self.info_dict['common_data']['yxb_cookie']
        url = 'https://www.51jt.com/api.jsp'
        self.session.headers.update({'x-YxbCookie': yxb_cookie, 'x-HWUserToken': yxb_token, 'x-uniqueId': unique_id})
        for i in range(1, 5):
            data = {"args":[yxb_token,1,3,i],
                    "argsclass":["java.lang.String","java.lang.Integer","java.lang.Integer","java.lang.Integer"],
                    "methodName":"getLoanListData","proxy":"LoanManagerV22"}
            response = self.session.post(url=url, data='json=' + json.dumps(data), verify=False,
                                         headers=self.session.headers)
            print(response.status_code)
            print(response.text)
            pair_data = {}
            if response.status_code !=200:
                continue
            else:
                data = json.loads(response.text)['value']
                for each in data:
                    loan_id = each['loanID']
                    loan_status = each['loanStatus']
                    loaner = each['name']
                    date = each['time']
                    amount = each['money']
                    interest = each['interest']
                    pair_data['loan_id'] = loan_id
                    pair_data['loan_status'] = loan_status
                    pair_data['loaner'] = loaner
                    pair_data['date'] = date
                    pair_data['amount'] = amount
                    pair_data['interest'] = interest
                    self.list_borrow.append(pair_data)
        # print(self.list_borrow)
    def get_wait_pay(self):
        unique_id = self.info_dict['common_data']['unique_id']
        yxb_token = self.info_dict['common_data']['yxb_token']
        yxb_cookie = self.info_dict['common_data']['yxb_cookie']
        url = 'https://www.51jt.com/api.jsp'
        self.session.headers.update({'x-YxbCookie': yxb_cookie, 'x-HWUserToken': yxb_token, 'x-uniqueId': unique_id})
        for i in range(1, 5):
            data = {"args": [yxb_token, 1, 2, i],
                    "argsclass": ["java.lang.String", "java.lang.Integer", "java.lang.Integer", "java.lang.Integer"],
                    "methodName": "getLoanListData", "proxy": "LoanManagerV22"}
            response = self.session.post(url=url, data='json=' + json.dumps(data), verify=False,
                                         headers=self.session.headers)
            pair_data = {}
            if response.status_code != 200:
                continue
            else:
                data = json.loads(response.text)['value']
                for each in data:
                    loan_id = each['loanID']
                    loan_status = each['loanStatus']
                    loaner = each['name']
                    date = each['time']
                    amount = each['money']
                    interest = each['interest']
                    pair_data['loan_id'] = loan_id
                    pair_data['loan_status'] = loan_status
                    pair_data['loaner'] = loaner
                    pair_data['date'] = date
                    pair_data['amount'] = amount
                    pair_data['interest'] = interest
                    self.list_borrow.append(pair_data)
    def main(self):
        self.get_common_data()
        # self.get_wait_pay()
        self.get_overdue()
        # self.get_paid_data()

    def inser_mongo(self):
        _id = '10' + '-' + str(uuid.uuid4())
        self.info_dict['borrow'] = self.list_borrow
        self.info_dict['_id'] = _id
        self.info_dict['id'] = dict_id['WYJD']
        self.info_dict['is_new'] = True
        self.info_dict['number'] = self.uname
        print(self.info_dict)
        self.debit.insert(self.info_dict)
if __name__ == '__main__':
    init = WYJD('18645145512','hwz5980279')
    init.main()
    init.inser_mongo()
