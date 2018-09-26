# -*- coding: UTF-8 -*-
"""
Created on 2017年9月25日
@author: Leo
"""


import random
from urllib.parse import quote_plus
from Config.config import *
from Config.transfer import *
import collections
import requests
from lxml import etree
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import logging


# 账单页面URL
MY_Url = 'https://my.alipay.com/portal/i.htm'
Bill_Url = 'https://consumeprod.alipay.com/record/advanced.htm'
# 登录页面URL(quote_plus的理由是会处理斜杠)
Login_Url = 'https://auth.alipay.com/login/index.htm?goto=' + quote_plus(MY_Url)
# Login_Url = 'https://auth.alipay.com/login/index.htm?goto=' + quote_plus(Bill_Url)

# User-agent
USER_AGENT = ['Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
              'Chrome/50.0.2661.102 UBrowser/6.1.3397.16 Safari/537.36',
              'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
              'Chrome/61.0.3163.100 Safari/537.36']

# 自定义 headers
HEADERS = {
    'User-Agent': random.choice(USER_AGENT),
    'Referer': 'https://consumeprod.alipay.com/record/advanced.htm',
    'Host': 'consumeprod.alipay.com',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Connection': 'keep-alive'
}

# 日志基本配置(同时写入到文件和输出到控制台)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')
logger = logging.getLogger()


# 支付宝账单信息
class AlipayBill(object):
    # headers, cookies, info_list: 存储账单信息的列表
    def __init__(self, headers, uname, upwd):
        # 初始化浏览器字段
        self.browser = None

        # 初始化headers
        self.headers = headers

        # 初始化用户名和密码
        self.username = uname
        self.password = upwd

        # requests的session对象
        self.session = requests.Session()

        # 将请求头添加到session之中
        self.session.headers = self.headers

        # cookie存储
        self.cookie = {}

        # 交易类别选项
        self.transfer_option = None

        # 账单筛选
        # (目前为自定义时间)
        # self.begin_date = "2017.07.14"
        # self.end_date = "2017.10.14"
        self.end_date, self.begin_date = get_front_or_after_month(month=-3)

    # 查看浏览器(用配置文件进行维护,智能化)
    # def choose_browser(self):
    #     # 读取自定义selenium配置文件
    #     browser_configure = json.load(open("C:\\Users\\Administrator\\Desktop\\Alipay-Spider-master\\conf\\selenium.conf"))
    #     if browser_configure['PhantomJs'] != "" and browser_configure['ChromeDriver'] != "":
    #         logging.info("请输入浏览器类型: (1和回车是phantomJs, 2是Google Chrome浏览器)")
    #         browser_choice = input()
    #         # 选择1
    #         if browser_choice == "" or browser_choice == "1":
    #             self._load_phantomjs(browser_configure)
    #         # 选择2
    #         elif browser_choice == "2":
    #             self._load_chrome(browser_configure)
    #         # 异常选择
    #         else:
    #             raise ValueError("浏览器类型错误,请重试....")
    #     else:
    #         if browser_configure['PhantomJs'] != "":
    #             logger.info("加载PhantomJs浏览器...")
    #             self._load_phantomjs(browser_configure)
    #         elif browser_configure['ChromeDriver'] != "":
    #             logger.info("加载Chrome浏览器...")
    #             self._load_chrome(browser_configure)
    #         else:
    #             raise ValueError("Selenium configuration load failed, please check your configuration!...")

    # # 加载PhantomJs
    # def _load_phantomjs(self, browser_configure):
    #     dcap = dict(DesiredCapabilities.PHANTOMJS)
    #     dcap['phantomjs.page.settings.userAgent'] = random.choice(USER_AGENT)
    #     self.browser = webdriver.PhantomJS(executable_path=browser_configure['PhantomJs'],
    #                                        service_log_path=browser_configure['LogPath'],
    #                                        desired_capabilities=dcap,
    #                                        port=browser_configure['Port'])
    #     # 判断浏览器是否初始化成功
    #     return self.browser is None if True else False

    # 加载Google Chrome
    def _load_chrome(self):
        self.browser = webdriver.Chrome(executable_path='chromedriver.exe')
        # 判断浏览器是否初始化成功
        return self.browser is None if True else False

    # 减慢账号密码的输入速度
    def close_browser(self):
        self.browser.close()
        return

    @staticmethod
    def _slow_input(ele, word):
        for i in word:
            # 输出一个字符
            ele.send_keys(i)
            # 随机睡眠0到1秒
            time.sleep(random.uniform(0, 0.5))

    # 获取cookies
    def get_cookies(self):
        # 浏览器初始化失败
        if self.browser is None:
            raise ValueError("Browser is not initialize!...")

        # 初始化浏览器对象
        self.browser.maximize_window()
        self.browser.get(Login_Url)
        self.browser.implicitly_wait(3)

        # 遇到问题 --- 1(概率出现,登录页面的选项卡默认扫码登录)
        self.browser.find_element_by_xpath('//*[@id="J-loginMethod-tabs"]/li[2]').click()

        # 用户名输入框
        username = self.browser.find_element_by_id('J-input-user')
        username.clear()
        logger.info('正在输入账号.....')
        self._slow_input(username, self.username)
        time.sleep(random.uniform(0.4, 0.8))

        # 密码输入框
        # xpath: //*[@id="password_container"]/input
        # password = self.browser.find_element_by_id('password_rsainput') # 官方貌似已经修改了前端页面(2017-11-2发现的)
        password = self.browser.find_element_by_xpath('//*[@id="password_container"]/input')
        password.clear()
        logger.info('正在输入密码....')
        self._slow_input(password, self.password)

        # 登录按钮
        # 隐藏Bug(1)：phantomJs在这里容易卡死...不知道为什么
        time.sleep(random.uniform(0.3, 0.5))
        self.browser.find_element_by_id('J-login-btn').click()

        # 输出当前链接
        logger.info("当前页面链接: " + self.browser.current_url)

        # 跳转下一个页面
        logger.info('正在跳转页面....')
        if "checkSecurity" in self.browser.current_url:
            logger.info("进入手机验证码页面")
            self.browser.get(self.browser.current_url)

            # 手机验证码输入框
            secure_code = self.browser.find_element_by_id("riskackcode")

            # 一次清空输入框
            secure_code.click()
            secure_code.clear()

            logger.info("输入验证码:")
            user_input = input()

            # 防止一些操作失误，二次清空输入框
            secure_code.click()
            secure_code.clear()

            # 开始输入用户提供的验证码
            self._slow_input(secure_code, user_input)

            # 验证码界面下一步按钮
            next_button = self.browser.find_element_by_xpath('//*[@id="J-submit"]/input')
            time.sleep(random.uniform(0.5, 1.2))
            next_button.click()

            logger.info("准备进入账单页面")
            logger.info("当前页面: " + self.browser.current_url)
            # self.browser.get(Bill_Url)
            self.browser.get(MY_Url)

            # 获取cookies转换成字典
            cookies = self.browser.get_cookies()

            # cookie字典
            cookies_dict = {}
            for cookie in cookies:
                if 'name' in cookie and 'value' in cookie:
                    cookies_dict[cookie['name']] = cookie['value']
            self.cookie = cookies_dict
            return True

        elif "login" in self.browser.current_url:
            logger.info("没有进入验证码界面,用户名密码错误,请重试")
            return False

        else:
            logger.info("没有进入验证码界面,进入账单页面")
            logger.info("当前页面: " + self.browser.current_url)
            self.browser.get(MY_Url)

            # 获取cookies转换成字典
            cookies = self.browser.get_cookies()

            # cookie字典
            cookies_dict = {}
            for cookie in cookies:
                if 'name' in cookie and 'value' in cookie:
                    cookies_dict[cookie['name']] = cookie['value']
            self.cookie = cookies_dict
            return True

    # set cookies 到 session
    def _set_cookies(self):
        cookie = self.cookie
        self.session.cookies.update(cookie)
        # 输出cookie
        logger.debug(self.session.cookies)

    # 判断登录状态
    def _login_status(self):
        # 添加 cookies
        self._set_cookies()
        status = self.session.get(MY_Url, timeout=5, allow_redirects=False).status_code
        logging.debug(status)
        return True

        # 以下注释和以上代码,在爬取中发现404依然能够保留登录状态并成功跳转.
        # if status == 200:
        #     return True
        # else:
        #     return False

    # 该方法用来确认元素是否存在，如果存在返回flag=true，否则返回false
    def _is_element_exist(self):
        try:
            self.browser.find_element_by_link_text('下一页')
            return True
        except Exception as err:
            logger.debug("判断是否存在下一页: " + str(err))
            return False

    # 翻页查询(参数is_next_page 控制是否有下一页)
    def _turn_page(self, option):
        # 先判断是否存在下一页的标签
        is_next_page = self._is_element_exist()
        logger.info("是否存在下一页: " + str(is_next_page))

        # 上一个版本用的是BeautifulSoup进行标签获取,现在改成用lxml(Etree) + Xpath获取

        html = self.browser.page_source
        selector = etree.HTML(html)

        # 选取的父标签
        trs = selector.xpath("//tbody//tr")

        try:
            # 加载数据库配置

            # 开始循环第一页
            for tr in trs:
                # 交易记录实体类
                transfer = Transfer()

                # 交易时间(年月日)
                time_tag = tr.xpath('td[@class="time"]/p/text()')
                time_list = (str(time_tag[0]).strip() + " " + str(time_tag[1]).strip()).split(" ")
                transfer.y_m_d = time_list[0].replace(".", "")

                # 交易时间(时分秒)
                transfer.h_m_s = time_list[1].replace(":", "") + "00"

                # memo标签(交易备注)
                try:
                    transfer.memo = str(tr.xpath('td[@class="memo"]/'
                                                 'div[@class="fn-hide content-memo"]/'
                                                 'div[@class="fn-clear"]/p[@class="memo-info"]/text()')[0]).strip()
                except IndexError:
                    logger.debug("Transfer memo exception: transfer memo is empty!")
                    transfer.memo = ""

                # 交易名称
                try:
                    transfer.name = str(tr.xpath('td[@class="name"]/p/a/text()')[0]).strip()
                except IndexError:
                    try:
                        transfer.name = str(tr.xpath('td[@class="name"]/p/text()')[0]).strip()
                    except IndexError:
                        logger.debug("Transfer name exception 2: Transfer name is empty!")
                        transfer.name = ""

                # 交易订单号(商户订单号和交易号)
                code = tr.xpath('td[@class="tradeNo ft-gray"]/p/text()')
                if "流水号" in code[0]:
                    transfer.serial_num = (str(code[0]).split(":"))[-1]
                    transfer.seller_code = ""
                    transfer.transfer_code = ""
                else:
                    code_list = str(code[0]).split(" | ")
                    transfer.serial_num = ""
                    transfer.seller_code = (str(code_list[0]).split(":"))[-1]
                    transfer.transfer_code = (str(code_list[-1]).split(":"))[-1]

                # 对方(转账的标签有不同...奇葩的设计)
                if transfer.memo == "":
                    try:
                        transfer.opposite = str(tr.xpath('td[@class="other"]/p[@class="name"]/span/text()')[0]).strip()
                    except IndexError:
                        transfer.opposite = str(tr.xpath('td[@class="other"]/p[@class="name"]/text()')[0]).strip()
                else:
                    try:
                        transfer.opposite = str(tr.xpath('td[@class="other"]/p[@class="name"]/span/text()')[0]).strip()
                    except IndexError:
                        transfer.opposite = str(tr.xpath('td[@class="other"]/p/text()')[0]).strip()

                # 金额
                transfer.money = str(tr.xpath('td[@class="amount"]/span/text()')[0]).replace(" ", "").replace("+", "")

                # 状态
                transfer.status = tr.xpath('td[@class="status"]/p[1]/text()')[0]

                # 用户
                transfer.user = self.username

                # 交易类型
                # print(option)
                # transfer.tag = option

                # 输出
                logger.info(transfer.get_order_dict())
                print(transfer.get_order_dict())

                # 写入到数据中

            # 判断是否存在下一页的标签
            if is_next_page:
                # 智能等待 --- 3

                # 抓取完当页的数据后,滚动事件到底部，点击下一页
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                # 智能等待 --- 4
                time.sleep(random.uniform(0.5, 0.9))

                # 点击下一页
                next_page_btn = self.browser.find_element_by_link_text('下一页')
                next_page_btn.click()
                self._turn_page(option)
            else:
                # 不存在下一页后返回
                return True

        except Exception as err:
            logger.debug(err.with_traceback(err))
            logger.error('抓取出错,页面数据获取失败')
            return False

    # 抓取数据
    def get_data(self):
        # 判断登录状态
        status = self._login_status()

        logger.info("当前页面: " + self.browser.current_url)

        # 上一个版本用的是BeautifulSoup进行标签获取,现在改成用lxml获取
        # html = self.browser.page_source
        # selector = etree.HTML(html)

        # 支付宝我的页面(2017-11-2 发现支付宝在个人中心的页面取消显示了花呗额度)
        # user_limit_money = selector.xpath('//div[@class="i-assets-body"]/div/p[1]/span/strong/text()')[0] + \
        #                    selector.xpath('//div[@class="i-assets-body"]/div/p[1]/span/strong/span/text()')[0]

        # //*[@id="J-assets-pcredit"]/div/div/div[2]/div/p[2]/span/strong
        # user_month_bill_info = "".join(
        #     str(selector.xpath('//div[@class="amount-des"]/p[2]/span[@class="highlight"]/strong')[0].
        #         xpath('string(.)')).split())

        # 用户花呗当前额度和全部额度的字典
        # 蚂蚁花呗的英文是Ant check later
        # issue 1 --- 用户花呗有临时额度的可能,或者用户修改了额度,存在数据库数据的版本问题
        # user_check_later = collections.OrderedDict()
        # user_check_later['user'] = self.username
        # # user_check_later['user_limit'] = user_limit_money
        # user_check_later['user_month_bill_info'] = user_month_bill_info
        # user_check_later['create_time'] = str(round(time.time() * 1000))

        # 先写入到数据库
        # mgo = Mgo(logger)
        # mgo.insert_data(data=user_check_later, collection_name="User")

        # 智能等待 --- 6
        time.sleep(random.uniform(0.2, 0.9))

        # 获取完后跳转到账单页面
        self.browser.find_element_by_xpath('//ul[@class="global-nav"]/li[@class="global-nav-item "]/a').click()

        if status:
            time.sleep(5)
            # 下拉框a标签点击事件触发
            self.browser.find_element_by_xpath('//div[@id="J-datetime-select"]/a[1]').click()

            # 选择下拉框的选项
            self.browser.find_element_by_xpath('//ul[@class="ui-select-content"]/li[@data-value="customDate"]').click()

            # 起始日期和最终日期的初始化
            begin_date_tag = "beginDate"
            end_date_tag = "endDate"

            # 设置起始日期
            remove_start_time_read_only = "document.getElementById('" + begin_date_tag + "')." \
                                                                                         "removeAttribute('readonly')"
            self.browser.execute_script(remove_start_time_read_only)
            ele_begin = self.browser.find_element_by_id(begin_date_tag)
            ele_begin.clear()
            self._slow_input(ele_begin, self.begin_date)

            # 智能等待 --- 1
            time.sleep(random.uniform(1, 2))

            # 设置结束日期
            remove_end_time_read_only = "document.getElementById('" + end_date_tag + "').removeAttribute('readonly')"
            self.browser.execute_script(remove_end_time_read_only)
            ele_end = self.browser.find_element_by_id(end_date_tag)
            ele_end.clear()
            self._slow_input(ele_end, self.end_date)

            # 智能等待 --- 2
            time.sleep(random.uniform(0.5, 0.9))

            # 选择交易分类
            self.browser.find_element_by_xpath('//div[@id="J-category-select"]/a[1]').click()

            # 选择交易分类项
            self._bill_option_control()

            # 智能等待 --- 3
            time.sleep(random.uniform(1, 2))

            # 按钮(交易记录点击搜索)
            self.browser.find_element_by_id("J-set-query-form").click()
            logger.info("跳转到自定义时间页面....")
            logger.info(self.browser.current_url)

            # 进行页面数据抓取
            self._turn_page(option=self.transfer_option)
        else:
            logger.error('抓取出错,登录失败!')

    # 选择账单选项的下拉列表(选择账单类别) --- 暂时不生效
    def next_bill_option(self):
        if self.transfer_option != 4:
            self.transfer_option += 1
        else:
            return True

    # 确认账单类型选项的下拉选项(目前只有购物,线下,还款,缴费)
    def _bill_option_control(self):
        # 购物 SHOPPING
        # 线下 OFFLINENETSHOPPING
        # 还款 CCR
        # 缴费 PUC_CHARGE
        # 全部 ALL
        self.browser.find_element_by_xpath(
            '//ul[@class="ui-select-content"]/li[@data-value="ALL"]').click()
    '''
        * 开关功能模块
        1. 关闭浏览器,退出爬虫模块
        2. 主启动模块,开始初始化爬虫
    '''
    # 关闭浏览器
    # def close_browser(self):
    #     self.browser.close()
    # 主启动类
    def main(self):
        # 加载用户名密码
        if (self.username == "" or self.username is None) or (self.password == "" or self.password is None):
            logger.info("请输入正确的账号和密码!")
            raise ValueError("Account or password is illegal!")
        # 选择日志等级(后期改为用参数进行选择)
        logging.error("日志等级为: INFO")
        logger.setLevel("INFO")
        # 选择爬取交易选项(以后可扩展为动态)
        # 初始化浏览器
        self._load_chrome()
        # 返回True值,初始化参数成功
        return True
def parser_spider():
    # 入口
    alipay = AlipayBill(headers=HEADERS, uname='18617126861', upwd='itolsou2601039')
    # 初始化一些选项和浏览器
    alipay.main()
    # 初始化结束后，开始登陆
    is_login = alipay.get_cookies()
    # 判断是否登录成功sms_code
    if is_login:
        # 登陆后开始获取数据
        alipay.get_data()
        # 关闭浏览器
        # alipay.close_browser()
        # 成功
        return True
    else:
        # 登录失败关闭浏览器
        # alipay.close_browser()
        # 失败
        return False
parser_spider()