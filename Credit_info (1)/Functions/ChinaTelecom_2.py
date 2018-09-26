import requests
from Config.config import *
import time
import json
import random
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import logging
from tools.jd_tools import save_image,open_image
import os
import pickle
from bs4 import BeautifulSoup
from Config.config import mongo_connect
import uuid
import sys
from PIL import Image
from io import StringIO

Login_Url = 'https://gd.189.cn/common/newLogin/newLogin/login.htm'

# User-agent
USER_AGENT = ['Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
              'Chrome/50.0.2661.102 UBrowser/6.1.3397.16 Safari/537.36',
              'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
              'Chrome/61.0.3163.100 Safari/537.36']
db = mongo_connect()['credit_info']
collection = db['consume_info']
# 自定义 headers
HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Host': 'gd.189.cn',
    'If-Modified-Since': 'Tue, 18 Sep 2018 09:59:50 GMT',
    'If-None-Match': "pv8d89167ed8e0e6f1581cf7b55417790f",
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'
}
list_contact = []
# 日志基本配置(同时写入到文件和输出到控制台)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')
logger = logging.getLogger()


class ChinaTelecom(object):
    def __init__(self, uname, upasswd):
        super(ChinaTelecom, self).__init__()
        self.session = requests.Session()
        self.session.headers = HEADERS
        # cookie存储
        self.page = 0
        self.uname = uname
        self.upasswd = upasswd
        self.captcha_url = 'https://ic.qq.com/pim/captcha.jsp?'
        self.operator_info = mongo_connect()['operator_info']
        self.info_dict = {}
    def _load_chrome(self):
        self.browser = webdriver.Chrome(executable_path='chromedriver.exe')
        # 判断浏览器是否初始化成功
        return self.browser is None if True else False

    def close_browser(self):
        self.browser.close()
        return

    # 减慢账号密码的输入速度
    @staticmethod
    def _slow_input(ele, word):
        for i in word:
            # 输出一个字符
            ele.send_keys(i)
            # 随机睡眠0到1秒
            time.sleep(random.uniform(0, 0.5))
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
    def login(self):
        end_num = random.random()
        time_now = int(time.time())
        headers = {
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Host': 'gd.189.cn',
            'Referer': 'https://gd.189.cn/common/newLogin/newLogin/login.htm',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'
        }

        self._load_chrome()
        if self.browser is None:
            raise ValueError("Browser is not initialize!...")

        # 初始化浏览器对象
        self.browser.maximize_window()
        self.browser.get(Login_Url)
        self.browser.implicitly_wait(3)
        # self.browser.find_element_by_css_selector('#l_pwType > span:nth-of-type(2) > label').click()
        # self.browser.find_element_by_id('id').click()
        # 用户名输入框
        print(self.browser.page_source)
        username = self.browser.find_element_by_id('account')
        username.clear()
        logger.info('正在输入账号.....')
        self._slow_input(username, self.uname)
        time.sleep(2)
        self.browser.find_element_by_id('password').click()
        time.sleep(random.uniform(0.4, 0.8))
        password = self.browser.find_element_by_id('password')
        password.clear()
        logger.info('正在输入密码....')
        self._slow_input(password, self.upasswd)
        captcha_url = 'https://gd.189.cn/nCheckCode?kkadf={}'.format(str(end_num))
        print(captcha_url)
        self.session.headers.update(headers)
        #获取到当前browser的cookie, 更新session
        cookies = self.browser.get_cookies()
        new_cookie = self.save_cookie(cookies)
        self.session.cookies.update(new_cookie)

        self.captcha_path = os.path.join('../Verify/images/China_Telecom/',
                                         'China_Telecom' + '-' + str(self.uname) + '-' + str(time_now) + '.jpg')

        captcha_res = self.session.get(captcha_url + str(time_now), verify=False, headers=headers)
        save_image(captcha_res, self.captcha_path)
        open_image(self.captcha_path)
        logger.info('请查看验证码')
        logging.info('请输入验证码, 验证码: ')
        self.browser.implicitly_wait(10)

        captcha_code = input()
        captcha = self.browser.find_element_by_css_selector('#loginCodeRand')
        self._slow_input(captcha, captcha_code)

        self.browser.implicitly_wait(5)
        self.browser.find_element_by_css_selector('#t_login').click()
        ccurrent_url = self.browser.current_url

        #更新COOKIE, 更新 SESSIONID


        current_window = self.browser.current_window_handle  # 获取当前窗口handle name
        all_window =self.browser.window_handles
        for window in all_window:
            if window != current_window:
                self.browser.switch_to.window(window)
        current_window = self.browser.current_window_handle

        cookies = self.browser.get_cookies()
        new_cookie = self.save_cookie(cookies)
        self.session.cookies.update(new_cookie)
        # self.get_user_info()
        #获取用户基本信息


    def get_user_info(self):
        _id = '2' + '-' + str(uuid.uuid4())
        id = int(dict_id['China_Telecom'])
        user_number = self.uname
        time.sleep(5)
        month_basic_fee = self.browser.find_element_by_id('averageCost').text
        month_basic_fee = clean_data(month_basic_fee)
        self.browser.find_element_by_css_selector('body > div.wrap.clearfix > div.contLeft > div > '
                                                  'div.menuMod > ul > li:nth-of-type(6) > a').click()
        time.sleep(5)
        print(self.browser.current_url)
        my_data = self.browser.find_element_by_css_selector('body > div.wrap.clearfix > div.contright > div:nth-of-type(1) > '
                                                  'div.mainCon.clearfix > div > a:nth-of-type(1)').get_attribute('href')
        self.browser.get(my_data)
        self.browser.implicitly_wait(10)
        print(self.browser.current_url)
        regis_id = self.browser.find_element_by_id('id_num_id').get_attribute('value')
        regis_id = clean_data(regis_id)
        regis_name = self.browser.find_element_by_id('cust_name_id').get_attribute('value')
        regis_name = clean_data(regis_name)
        regis_address = self.browser.find_element_by_id('id_addr_id').get_attribute('value')
        regis_address = clean_data(regis_address)

        #查询入网日期
        #返回至用户中心
        self.browser.find_element_by_css_selector('body > div.wrap.content > div.left > div > div > div > ul > li:nth-of-type(6)').click()
        self.browser.implicitly_wait(10)
        self.browser.find_element_by_css_selector('body > div.wrap.clearfix > div.contLeft > div > '
                                                  'div.userInfoNew.clearfix.none > div.heaPor.fl > a').click()
        time.sleep(5)
        regis_date = self.browser.find_element_by_id('AdmissionDate').text
        regis_date = clean_data(regis_date)
        self.regis_date = regis_date[0:4] + '-' + regis_date[4:6] + '-' + regis_date[6:8]
        int_regis_date = date_to_timestamp(regis_date)

        cookies = self.browser.get_cookies()
        new_cookie = self.save_cookie(cookies)
        self.session.cookies.update(new_cookie)

        self.info_dict['_id'] = _id
        self.info_dict['id'] = id
        self.info_dict['user_number'] = user_number
        self.info_dict['regis_id'] = regis_id
        self.info_dict['regis_name'] = regis_name
        self.info_dict['regis_address'] = regis_address
        self.info_dict['regis_date'] = int_regis_date
        self.info_dict['month_basic_fee'] = month_basic_fee

    def call(self):
        time.sleep(5)
        self.browser.find_element_by_css_selector('body > div.wrap.clearfix > div.contLeft > div > div.menuMod > ul > li:nth-of-type(2) > a').click()
        time.sleep(5)
        next = self.browser.find_element_by_css_selector('body > div.wrap.clearfix > div.contright > div:nth-of-type(1) > '
                                                  'div.mainCon.clearfix > div > a:nth-of-type(3)').get_attribute('href')
        self.browser.get(next)
        time.sleep(5)

        list_call_infos = []
        months_list = []
        self.regis_date = '20171225'
        query_dates = date_delta(self.regis_date)
        check_sign = 0
        for query_date in query_dates:
            list_month_total_call = []
            begin_date = query_date[0]
            end_date = query_date[1]
            #去掉只读, 强制改为填充
            js_begin ="$(\"input[placeholder='点击选择开始时间']\").removeAttr('readonly');$(\"input[placeholder='点击选择开始时间']\").attr('value',{})".format(begin_date)
            self.browser.execute_script(js_begin)
            js_end = "$(\"input[placeholder='点击选择结束时间']\").removeAttr('readonly');$(\"input[placeholder='点击选择结束时间']\").attr('value',{})".format(end_date)
            self.browser.execute_script(js_end)
            #第一次需要短信验证码, 后几次查询不需要
            if check_sign == 0:
                #点击选择短信验证码
                send_msg = self.browser.find_element_by_id('idSearchVerifyCode').click()
                time.sleep(2)
                alert = self.browser.switch_to.alert
                alert.accept()

                logger.info('请查收短信验证码: ')
                msg_code = input()
                code_input = self.browser.find_element_by_id('verifyCode_dx')
                self._slow_input(code_input, msg_code)
                check_sign += 1
            self.browser.find_element_by_id('queryBtn').click()
            time.sleep(2)
            page_source = self.browser.page_source
            if '查询时间验证失败' in str(page_source):
                logger.error('该月无消费记录')
                continue
            else:
                wb_data = BeautifulSoup(page_source, 'lxml')
                call_info_list = []
                fee = wb_data.select('#total_cost').text

                month = begin_date[4:6]
                months_list.append(month)
                month_call_total_time = wb_data.select('#total_time')
                int_month_call_total_time = minute_to_seconds(month_call_total_time)
                call_total_num = 0
                # 数据按照月份做成字典
                #中国电信没有通话id
                call_areas = wb_data.select('#rstBody > tr > td:nth-of-type(8)')
                call_ids = [0] * len(call_areas)
                voice_calls = ['语音电话'] * len(call_areas)
                call_types = wb_data.select('#rstBody > tr > td:nth-of-type(7)')
                domestic_calls = wb_data.select('#rstBody > tr > td:nth-of-type(2)')
                vpn_calls = ['VPN通话'] * len(call_areas)
                called_areas = [''] * len(call_areas)
                call_dates = wb_data.select('#rstBody > tr > td:nth-of-type(4)')
                call_nums = wb_data.select('#rstBody > tr > td:nth-of-type(3)')
                call_durations = wb_data.select('#rstBody > tr > td:nth-of-type(5)')
                call_fees = wb_data.select('#rstBody > tr > td:nth-of-type(6)')

                for call_area, call_id, voice_call, call_type, domestic_call, vpn_call, called_area, \
                    call_date, call_num, call_duration, call_fee \
                        in zip(call_areas, call_ids, voice_calls,call_types,domestic_calls,
                               vpn_calls,called_areas,call_dates, call_nums,call_durations,call_fees):
                    each_call_info = {}
                    call_id = call_id
                    call_area = call_area.text
                    voice_call = voice_call
                    call_type = call_type.text
                    domestic_call = domestic_call.text
                    vpn_call = vpn_call
                    called_area = called_area
                    call_day = call_date.text[0:10]
                    call_time = call_date.text[11:]
                    call_datetime = date_to_timestamp(call_day + ' ' + call_time)
                    call_num = call_num.text
                    call_duration = call_duration.text
                    call_fee = call_fee.text

                    each_call_info['call_id'] = call_id
                    each_call_info['call_area'] = call_area
                    each_call_info['voice_call'] = voice_call
                    each_call_info['call_type'] = call_type
                    each_call_info['domestic_call'] = domestic_call
                    each_call_info['vpn_call'] = vpn_call
                    each_call_info['called_area'] = called_area
                    each_call_info['call_date'] = call_date.text
                    each_call_info['call_time'] = call_time
                    each_call_info['call_datetime'] = call_datetime
                    each_call_info['call_num'] = call_num
                    each_call_info['call_duration'] = minute_to_seconds(call_duration)
                    each_call_info['call_fee'] = call_fee
                    list_month_total_call.append(call_num)
                    call_info_list.append(each_call_info)
                call_total_num = len(list_month_total_call)
                dict_each_month = {
                    'month': month,
                    'call_info': call_info_list
                }

                dict_each_month.update({'month_count': {'month_fee': fee, 'call_total_time': int_month_call_total_time,
                                                        'call_total_num': call_total_num}})
                list_call_infos.append(dict_each_month)
        self.info_dict['_id'] = '2' + '-' + str(uuid.uuid4())
        self.info_dict['id'] = int(dict_id['China_Telecom'])
        self.info_dict['call_info'] = list_call_infos
        self.info_dict['is_new'] = True
        self.info_dict['source'] = dict_id['China_Telecom']
        self.info_dict['captcha'] = self.captcha_path
        print(self.info_dict)
        self.operator_info.insert(self.info_dict)



if __name__ == '__main__':
    init = ChinaTelecom('18127013650', '152913')
    init.login()
    # init.validate_msg()
    # init.send_msg()
    init.call()