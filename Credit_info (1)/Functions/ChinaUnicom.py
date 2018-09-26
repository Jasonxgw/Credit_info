# -*- coding:utf-8 -*-
"""
@author : payne
@date : 2018-08-24
@China_Unicom 用户信息
"""

import requests
import logging
import json
import re
from http import cookiejar
from Config.config import *
import uuid
import time

class China_Unicom(object):
    def __init__(self):
        super(China_Unicom, self).__init__()
        self.header = {
            'Accept': 'text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Host': 'uac.10010.com',
            'Referer': 'https://uac.10010.com/portal/homeLogin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
            'Upgrade-Insecure-Requests': '1',
            'X-Requested-With': 'XMLHttpRequest'
        }
        self.info_dict = {}
        self.post_id = '000100030001'
        self.session = requests.session()
        self.session.headers = self.header.copy()
        self.session.cookies = cookiejar.LWPCookieJar('cookies.txt')
        self.operator_info = mongo_connect()['operator_info']

    #登录主函
    def login(self, phone_num, server_pwd):
        flag = 0
        try:
            self.session.cookies.load(ignore_discard=True)
            flag = 1
        except FileNotFoundError:
            flag = 0
        if flag:
            s = self.check_verify(phone_num)
            if s['resultCode'] == 'false' and s['ckCode'] == '2':
                self.send_message(phone_num)
                self.login_first(phone_num, server_pwd)
                self.check_login()
            else:
                self.login_first(phone_num, server_pwd, need_verify=2)
                self.check_login()
        else:
            self.check_verify(phone_num)
            self.send_message(phone_num)
            self.login_first(phone_num, server_pwd)
            self.check_login()

    def check_verify(self, phone_num):
        check_url = 'https://uac.10010.com/portal/Service/CheckNeedVerify?' \
                    'callback=jQuery17200957458793685022_{0}&' \
                    'userName={1}&pwdType=01&_={2}'.format(int(time.time() * 1000),
                                                           phone_num,
                                                           int(time.time() * 1000))
        needVerify = self.session.get(url=check_url, headers=self.session.headers)
        logging.info('needVerify: %s' % needVerify.status_code)
        s = eval(re.match(r'^.*?({.*?}).*$', needVerify.text).group(1))
        return s

    #触发验证码
    def send_message(self, phone_num):
        send_message_url = 'https://uac.10010.com/portal/Service/SendCkMSG?' \
                           'callback=jQuery172036837534689129425_{0}&' \
                           'req_time={1}&mobile={2}&_={3}'.format(int(time.time() * 1000),
                                                                  int(time.time() * 1000),
                                                                  phone_num,
                                                                  int(time.time() * 1000))
        resp_msg = self.session.get(url=send_message_url, headers=self.session.headers)
        logging.info('resp_msg: %s' % resp_msg.text)

    # 单用户多次访问判断session是否在线
    def login_first(self, phone_num, server_password, need_verify=1):
        if need_verify == 1:
            self.verifyCode = input('请输入验证码：')
            get_url = 'https://uac.10010.com/portal/Service/MallLogin?' \
                      'callback=jQuery17207043599656300588_{0}&' \
                      'req_time={1}0&' \
                      'redirectURL=http%3A%2F%2Fwww.10010.com%2Fnet5%2F&' \
                      'userName={2}&' \
                      'password={3}&' \
                      'pwdType=01&' \
                      'productType=01&' \
                      'redirectType=03&' \
                      'rememberMe=1&' \
                      'verifyCKCode={4}&' \
                      '_={5}'.format(int(time.time() * 1000),
                                     int(time.time() * 1000),
                                     phone_num,
                                     server_password,
                                     self.verifyCode,
                                     int(time.time() * 1000))
            login_resp = self.session.get(get_url, headers=self.session.headers)
            logging.info('login_resp: %s' % login_resp.status_code)
        elif need_verify == 2:
            get_url = 'https://uac.10010.com/portal/Service/MallLogin?' \
                      'callback=jQuery17207043599656300588_{0}&' \
                      'req_time={1}0&' \
                      'redirectURL=http%3A%2F%2Fwww.10010.com%2Fnet5%2F&' \
                      'userName={2}&' \
                      'password={3}&' \
                      'pwdType=01&' \
                      'productType=01&' \
                      'redirectType=03&' \
                      'rememberMe=1&' \
                      '_={4}'.format(int(time.time() * 1000),
                                     int(time.time() * 1000),
                                     phone_num,
                                     server_password,
                                     int(time.time() * 1000))
            login_resp = self.session.get(get_url, headers=self.session.headers)
            logging.info('login_resp: %s' % login_resp.status_code)

    #每次服务器都会判定用户是否在登陆状态
    def check_login(self):
        check_login_common_url = 'http://www.10010.com/mall/service/common/l?_={0}'.format(int(time.time() * 1000))
        self.session.headers.update({
            'Host': 'www.10010.com',
            'Referer': 'http://www.10010.com/net5/036/',
        })
        check_login_common_resp = self.session.post(check_login_common_url, headers=self.session.headers)
        logging.info('check_login_common_resp: %s' % check_login_common_resp.status_code)

        self.user_phone_detail()

        self.session.headers.update({
            'Host': 'iservice.10010.com',
            'Origin': 'http://iservice.10010.com',
            'Referer': 'http://iservice.10010.com/e4/query/bill/call_dan-iframe.html?menuCode=000100030001',
        })
        check_login_url = 'http://iservice.10010.com/e3/static/check/checklogin/?_={0}'.format(int(time.time() * 1000))
        check_login_resp = self.session.post(check_login_url, headers=self.session.headers)
        logging.info('check_login_resp: %s' % check_login_resp.status_code)

    def user_phone_detail(self):  # 待确认是否需要请求
        user_phone_detail_url = 'http://iservice.10010.com/e4/query/bill/call_dan-iframe.html?' \
                                'menuCode=000100030001'
        user_phone_detail_resp = self.session.get(user_phone_detail_url, headers=self.session.headers)
        logging.info('user_phone_detial_resp: %s' % user_phone_detail_resp.status_code)

    #用户基本信息
    def get_user_info(self):
        user_info_url = 'http://iservice.10010.com/e3/static/query/searchPerInfo/?_={}'.format(int(time.time() * 1000))
        response = self.session.post(user_info_url, headers=self.session.headers)

        json_data = json.loads(response.text)
        if json_data:
            _id = '1' + '-' + str(uuid.uuid4())
            detail_data = json_data['result']['MyDetail']
            fee_data = json_data['packageInfo']
            user_number = detail_data.get('usernumber')
            regis_id = detail_data.get('certnum')
            regis_name = detail_data.get('custname')
            regis_address = detail_data.get('certaddr')
            self.regis_date = detail_data.get('opendate')
            int_regis_date = date_to_timestamp(self.regis_date)
            product_name = detail_data.get('productname')
            if product_name == '腾讯大王卡':
                month_basic_fee = fee_data['productInfo'][0]['productFee']
            else:
                month_basic_fee = fee_data['productInfo'][0]['packageInfo'][0]['discntInfo'][0]['discntFee']
            self.info_dict['_id'] = _id
            self.info_dict['id'] = int(dict_id['China_Unicom'])
            self.info_dict['user_number'] = user_number
            self.info_dict['regis_id'] = regis_id
            self.info_dict['regis_name'] = regis_name
            self.info_dict['regis_address'] = regis_address
            self.info_dict['regis_date'] = int_regis_date
            self.info_dict['month_basic_fee'] = month_basic_fee

        else:
            logging.error('用户登录状态错误，请重新登陆')
            exit(0)
    # 提交验证码
    def submit_check_message_num(self):
        call_detail = 'http://iservice.10010.com/e3/static/query/verificationSubmit?_={0}&' \
                      'accessURL=http://iservice.10010.com/e4/query/bill/call_dan-iframe.html?' \
                      'menuCode=000100030001&menuid=000100030001'.format(int(time.time() * 1000))

        check_message_num_resp = self.session.post(call_detail, data={'inputcode': self.verifyCode , 'menuId': self.post_id})

    # 通话详情
    def call_info(self):
        list_call_infos = []
        months_list = []
        call_detail = 'http://iservice.10010.com/e3/static/query/callDetail?_={0}&'
        'accessURL=http://iservice.10010.com/e4/query/bill/call_dan-iframe.html?'
        'menuCode=000100030001&menuid=000100030001'.format(int(time.time() * 1000)),
        # 根据开户时间计算查询日期，最多查询6个月内，不足6个月按照查询开户时间到当前日期
        query_dates = date_delta(self.regis_date)

        for query_date in query_dates:
            call_info_list = []
            begin_date = query_date[0]
            end_date = query_date[1]
            data = {'pageNo': '1', 'pageSize': 100, 'beginDate': begin_date, 'endDate': end_date}
            response = self.session.post(call_detail, headers=self.session.headers, data=data)
            json_data = json.loads(response.text)
            fee = json_data['alltotalfee']
            month = begin_date[4:6]
            months_list.append(month)
            month_call_total_time = json_data['callTotaltime']
            int_month_call_total_time = minute_to_seconds(month_call_total_time)
            call_total_num = json_data['pageMap']['totalCount']
            regis_id =  json_data['userInfo']['natureQueryNumberInfo']['part_id']
            regis_id = re.search('\d-(\d+)', regis_id).group(1)
            self.info_dict.update({'regis_id':regis_id})
            #数据按照月份做成字典
            for call_history in json_data['pageMap']['result']:
                each_call_info = {}
                call_id = call_history.get('cellid', ' ')
                call_area = call_history['calledhome']
                voice_call = call_history['thtypeName']
                call_type = call_history.get('calltypeName', ' ')
                domestic_call = call_history.get('landtype', ' ')
                vpn_call = call_history.get('romatypeName', ' ')
                called_area = call_history.get('homeareaName', ' ')
                call_date = call_history.get('calldate',' ')
                call_time = call_history.get('calltime',' ')
                call_datetime = date_to_timestamp(call_date + ' ' + call_time)
                call_num = call_history.get('othernum')
                call_duration = call_history.get('calllonghour', ' ')
                call_fee = call_history.get('totalfee', ' ')

                each_call_info['call_id'] = call_id
                each_call_info['call_area'] = call_area
                each_call_info['voice_call'] = voice_call
                each_call_info['call_type'] = call_type
                each_call_info['domestic_call'] = domestic_call
                each_call_info['vpn_call'] = vpn_call
                each_call_info['called_area'] = called_area
                each_call_info['call_date'] = call_date
                each_call_info['call_time'] = call_time
                each_call_info['call_datetime']  = call_datetime
                each_call_info['call_num'] = call_num
                each_call_info['call_duration'] = minute_to_seconds(call_duration)
                each_call_info['call_fee'] = call_fee

                call_info_list.append(each_call_info)
            dict_each_month = {
                'month':month,
                'call_info':call_info_list
            }

            dict_each_month.update({'month_count': {'month_fee':fee, 'call_total_time':int_month_call_total_time,
                                                    'call_total_num':call_total_num}})
            list_call_infos.append(dict_each_month)
        self.info_dict['call_info'] = list_call_infos
        self.info_dict['is_new'] = True
        self.info_dict['source'] = dict_id['China_Unicom']
        self.operator_info.insert(self.info_dict)


def main_china_unicom():
    if __name__ == '__main__':
        init = China_Unicom()
        init.login(18617126861, 152913)
        init.get_user_info()
        init.submit_check_message_num()
        init.call_info()
