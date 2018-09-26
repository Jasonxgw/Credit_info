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

Login_Url = 'https://ic.qq.com/pim/login.jsp'

# User-agent
USER_AGENT = ['Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
              'Chrome/50.0.2661.102 UBrowser/6.1.3397.16 Safari/537.36',
              'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
              'Chrome/61.0.3163.100 Safari/537.36']
db = mongo_connect()['credit_info']
collection = db['QQIC']
# 自定义 headers
HEADERS = {
    'User-Agent': random.choice(USER_AGENT),
    'Referer': 'https://ic.qq.com/pim/login.jsp',
    # 'Host': 'consumeprod.alipay.com',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Connection': 'keep-alive',
    # ':authority': 'ic.qq.com',
    # ':method': 'GET',
    # ':path': '/pim/captcha.jsp?1536284652246',
    # ':scheme': 'https'
}
list_contact = []
# 日志基本配置(同时写入到文件和输出到控制台)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')
logger = logging.getLogger()


class QQIC(object):
    def __init__(self, uname, upasswd):
        super(QQIC, self).__init__()
        self.session = requests.Session()
        self.session.headers = HEADERS
        # cookie存储
        self.page = 0
        self.uname = uname
        self.upasswd = upasswd
        self.captcha_url = 'https://ic.qq.com/pim/captcha.jsp?'
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
        time_now = int(time.time() * 100)
        headers = {
            'User-Agent': random.choice(USER_AGENT),
            'Referer': 'https://ic.qq.com/pim/login.jsp',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Connection': 'keep-alive',
            'authority': 'ic.qq.com',
            'method': 'GET',
            'path': '/pim/captcha.jsp?{}'.format(str(time_now)),
            'scheme': 'https'
        }
        self.session.headers.update(headers)
        self._load_chrome()
        if self.browser is None:
            raise ValueError("Browser is not initialize!...")

        # 初始化浏览器对象
        self.browser.maximize_window()
        self.browser.get(Login_Url)
        self.browser.implicitly_wait(3)

        self.captcha_path = os.path.join('../Verify/images/QQIC',
                                    'QQIC' + '-' + str(self.uname) + '-' + str(time_now) + '.jpg')

        cookies = self.browser.get_cookies()
        new_cookie = self.save_cookie(cookies)
        self.session.cookies.update(new_cookie)
        captcha_res = self.session.get(self.captcha_url + str(time_now), verify=False)
        save_image(captcha_res, self.captcha_path)

        self.browser.find_element_by_class_name('tab-tel').click()
        # 用户名输入框
        username = self.browser.find_element_by_id('input_mobile')
        username.clear()
        logger.info('正在输入账号.....')
        self._slow_input(username, self.uname)
        time.sleep(random.uniform(0.4, 0.8))
        password = self.browser.find_element_by_id('input_password')
        password.clear()
        logger.info('正在输入密码....')
        self._slow_input(password, self.upasswd)
        open_image(self.captcha_path)
        logger.info('请查看验证码')
        logging.info('请输入验证码, 验证码: ')
        self.browser.implicitly_wait(10)
        captcha_code = input()
        captcha = self.browser.find_element_by_id('input_verify')
        self._slow_input(captcha, captcha_code)
        time.sleep(5)
        self.browser.find_element_by_css_selector('#login_button').click()
        ccurrent_url = self.browser.current_url
        if ccurrent_url != 'https://ic.qq.com/mobile_login.jsp':
            logger.error('图形验证码或者密码错误, 请重试')
            self.close_browser()
            self.login()
        else:
            self.sms_code()

    def sms_code(self):
        logger.info('进入短信验证码阶段')
        self.browser.implicitly_wait(5)
        logger.info("当前页面链接: " + self.browser.current_url)

        self.browser.find_element_by_css_selector(
            '#contVerifyForm > div > div.cnt > div.v > input.b-btn.send-code').click()
        time.sleep(2)
        self.browser.find_element_by_css_selector('body > div.ui-dialog.ui-widget.ui-widget-content.ui-corner-'
                                                  'all.ui-front.ui-dialog-alert.ui-dialog-buttons.ui-draggable > '
                                                  'div.ui-dialog-buttonpane.ui-widget-content.ui-helper-clearfix > '
                                                  'div > button').click()

        logger.info('短信验证码已发送, 请查收')
        sms = self.browser.find_element_by_id('verifyCode')
        sms.clear()
        logger.info('请输入短信验证码：')
        sms_code = input()
        self._slow_input(sms, sms_code)
        self.browser.implicitly_wait(5)
        self.browser.find_element_by_css_selector('#contVerifyForm > div > div.cnt > input').click()
        time.sleep(2)
        if self.browser.current_url == 'https://ic.qq.com/mobile_login.jsp':
            logger.error('验证码输入有误或已过期, 请60S后重试')
            time.sleep(2)
            self.browser.find_elements_by_class_name('ui-button-text')[-1].click()

            time.sleep(65)
            self.sms_code()
        else:
            logger.info('登陆成功, 开始获取信息...')
    def _is_element_exist(self):
        try:
            self.browser.find_element_by_css_selector('#contactsPage > div > div.page.page-contact > a.icons.icon-page-next')
            return True
        except Exception as err:
            logger.debug("判断是否存在下一页: " + str(err))
            return False


    def get_data(self):
        is_next_page = self._is_element_exist()
        logger.info("是否存在下一页: " + str(is_next_page))
        if is_next_page:
            self.page += 1
            contact_url = 'https://ic.qq.com/pim/contact.jsp#list/-1/{}/50/ASC/name/0'.format(str(self.page))
            self.browser.get(contact_url)
            self.browser.implicitly_wait(5)
            response = self.browser.page_source
            wb_data = BeautifulSoup(response, 'lxml')
            names = wb_data.select('a.logClass.view')
            numbers = wb_data.select('#contactsBody > tr > td:nth-of-type(5)')

            for each_name, each_number in zip(names, numbers):
                name = each_name
                number = each_number
                dict_contact = {
                    'name':clean_data(str(name.text)),
                    'number':clean_data(str(number.text))
                }
                list_contact.append(dict_contact)
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # 智能等待 --- 4
            time.sleep(random.uniform(0.5, 0.9))
            # 点击下一页
            try:
                next_page_btn = self.browser.find_element_by_css_selector('#contactsPage > div > div.page.page-contact > a.icons.icon-page-next')
                next_page_btn.click()
                self.get_data()
            except Exception:
                logger.info('没有下一页了')

        contact = list_contact
        self.info_dict['contact'] = contact
        self.close_browser()
    def inser_mongo(self):
        _id = '9' + '-' + str(uuid.uuid4())
        self.info_dict['_id'] = _id
        self.info_dict['id'] = dict_id['QQTongXunLu']
        self.info_dict['is_new'] = True
        self.info_dict['number'] = self.uname
        self.info_dict['captcha'] = self.captcha_path
        collection.insert(self.info_dict)
def main():
    init = QQIC('13380318940','a2011123406')
    init.login()
    init.get_data()
    init.inser_mongo()

if __name__ == '__main__':
    main()