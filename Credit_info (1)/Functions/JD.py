# -*- coding: utf-8 -*-
import uuid
from Config.config import *
import datetime
import pickle
from bs4 import BeautifulSoup
from tools.jd_tools import *
import traceback

class JD(object):

    def __init__(self):
        self.username = ''
        self.nick_name = ''
        self.is_login = False
        self.risk_control = ''
        self.item_cat = dict()
        self.headers = {
            'Host': 'passport.jd.com',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        self.consume_info = mongo_connect()['consume_info']
        self.info_dict = {}
        self.sess = requests.session()
        try:
            self._load_cookies()
        except Exception as e:
            pass

    def _load_cookies(self):
        cookies_file = ''
        for name in os.listdir('./cookies'):
            if name.endswith('.cookies'):
                cookies_file = './cookies/{0}'.format(name)
                break
        with open(cookies_file, 'rb') as f:
            local_cookies = pickle.load(f)
        self.sess.cookies.update(local_cookies)
        self.is_login = self._validate_cookies()

    def _save_cookies(self):
        cookies_file = './cookies/{0}.cookies'.format(self.nick_name)
        directory = os.path.dirname(cookies_file)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(cookies_file, 'wb') as f:
            pickle.dump(self.sess.cookies, f)

    def _validate_cookies(self):  # True -- cookies is valid, False -- cookies is invalid
        # user can't access to order list page (would redirect to login page) if his cookies is expired
        url = 'https://order.jd.com/center/list.action'
        payload = {
            'rid': str(int(time.time() * 1000)),
        }
        try:
            resp = self.sess.get(url=url, params=payload, allow_redirects=False)
            return True if resp.status_code == requests.codes.OK else False
        except Exception as e:
            print(get_current_time(), e)
            return False

    def _need_auth_code(self, username):
        url = 'https://passport.jd.com/uc/showAuthCode'
        data = {
            'loginName': username,
        }
        payload = {
            'version': 2015,
            'r': random.random(),
        }
        resp = self.sess.post(url, params=payload, data=data, headers=self.headers)
        if not response_status(resp):
            print('获取是否需要验证码失败')
            return False

        js = json.loads(resp.text[1:-1])  # ({"verifycode":true})
        return js['verifycode']

    def _get_auth_code(self, uuid):
        image_file = os.path.join(os.getcwd(), 'jd_authcode.jpg')

        url = 'https://authcode.jd.com/verify/image'
        payload = {
            'a': 1,
            'acid': uuid,
            'uid': uuid,
            'yys': str(int(time.time() * 1000)),
        }
        self.headers['Host'] = 'authcode.jd.com'
        self.headers['Referer'] = 'https://passport.jd.com/uc/login'
        resp = self.sess.get(url, params=payload, headers=self.headers)
        if not response_status(resp):
            print('获取验证码失败')
            return ''

        save_image(resp, image_file)
        open_image(image_file)
        return input('验证码:')

    def _get_login_page(self):
        url = "https://passport.jd.com/new/login.aspx"
        page = self.sess.get(url, headers=self.headers)
        return page

    def _get_login_data(self):
        page = self._get_login_page()
        soup = BeautifulSoup(page.text, "html.parser")
        input_list = soup.driverect('.form input')

        data = dict()
        data['sa_token'] = input_list[0]['value']
        data['uuid'] = input_list[1]['value']
        data['_t'] = input_list[4]['value']
        data['loginType'] = input_list[5]['value']
        data['pubKey'] = input_list[7]['value']
        # eid & fp are generated by local javascript code according to browser environment
        data['eid'] = 'UHU6KVDJS7PNLJUHG2ICBFACVLMEXVPQUGIK2QVXYMSN45BIEMUSICVLTYQYOZYZN2KWHV3WQWMFH4QPED2DVQHUXE'
        data['fp'] = '536e2679b85ddea9baccc7b705f2f8e0'
        return data

    def login_by_username(self):
        if self.is_login:
            print(get_current_time(), '登录成功')
            return

        username = input('账号:')
        password = input('密码:')
        if (not username) or (not password):
            print(get_current_time(), '用户名或密码不能为空')
            return
        self.username = username

        data = self._get_login_data()
        uuid = data['uuid']

        auth_code = ''
        if self._need_auth_code(username):
            print(get_current_time(), '本次登录需要验证码')
            auth_code = self._get_auth_code(uuid)
        else:
            print(get_current_time(), '本次登录不需要验证码')

        login_url = "https://passport.jd.com/uc/loginService"
        payload = {
            'uuid': uuid,
            'version': 2015,
            'r': random.random(),
        }
        data['authcode'] = auth_code
        data['loginname'] = username
        data['nloginpwd'] = encrypt_pwd(password)
        self.headers['Host'] = 'passport.jd.com'
        self.headers['Origin'] = 'https://passport.jd.com'
        self.headers['X-Requested-With'] = 'XMLHttpRequest'
        resp = self.sess.post(url=login_url, data=data, headers=self.headers, params=payload)

        if not response_status(resp):
            print(get_current_time(), '登录失败')
            return False

        if not self._get_login_result(resp):
            return False

        # login success
        print(get_current_time(), '登录成功')
        self._save_cookies()
        self.is_login = True
        return True

    def _get_login_result(self, resp):
        js = parse_json(resp.text)
        error_msg = ''
        if 'success' in js:
            # {"success":"http://www.jd.com"}
            return True
        elif 'emptyAuthcode' in js:
            # {'_t': '_t', 'emptyAuthcode': '请输入验证码'}
            # {'_t': '_t', 'emptyAuthcode': '验证码不正确或验证码已过期'}
            error_msg = js['emptyAuthcode']
        elif 'username' in js:
            # {'_t': '_t', 'username': '账户名不存在，请重新输入'}
            # {'username': '服务器繁忙，请稍后再试', 'venture': 'xxxx', 'p': 'xxxx', 'ventureRet': 'http://www.jd.com/', '_t': '_t'}
            if js['username'] == '服务器繁忙，请稍后再试':
                error_msg = js['username'] + '(预计账户存在风险，需短信激活)'
            else:
                error_msg = js['username']
        elif 'pwd' in js:
            # {'pwd': '账户名与密码不匹配，请重新输入', '_t': '_t'}
            error_msg = js['pwd']
        else:
            error_msg = js
        print(get_current_time(), error_msg)
        return False
    #获取京东白条（开通状态，剩余额度，总额度）
    def get_jd_credit(self):
        url = 'https://trade.jr.jd.com/async/creditData.action?_dc=1535699103795'
        self.headers['Host'] = 'trade.jr.jd.com'
        self.headers['Referer'] = 'https://trade.jr.jd.com/centre/browse.action'
        try:
            resp = self.sess.get(url=url, headers=self.headers)
            if not response_status(resp):
                print(get_current_time(), '获取订单页信息失败')
                return
            else:
                json_data = json.loads(resp.text)
                # 3 开通了京东白条 2 未开通京东白条
                jd_credit_status = json_data['actStatus']
                amount = json_data['availableLimit']
                need_2_pay = json_data['creditWaitPay']
                balanced = float(amount) - float(need_2_pay)
                self.info_dict['credit_status'] = dict_jd_credit[jd_credit_status]
                self.info_dict['balanced'] = str(balanced) + '元' + '/' + str(amount) + '元'

        except Exception as e:
            print(get_current_time(), traceback.format_exc())
        return
    #实时小白信用值
    def get_bai_score(self):
        url = 'https://baitiao.jd.com/v3/ious/score_getScoreInfo?rnd=1535937628059'
        self.headers['Host'] = 'baitiao.jd.com'
        self.headers['Referer'] = 'https://baitiao.jd.com/v3/ious/list'
        try:
            resp = self.sess.get(url=url, headers=self.headers)
            if not response_status(resp):
                print(get_current_time(), '获取小白信用值错误')
                return
            else:
                bai_score = float(resp.text.strip())
                self.info_dict['bai_score'] = bai_score
        except Exception as e:
            print(get_current_time(), e)
        return
    #银行卡信息
    def get_card_info(self):
        #请求头不对会一直重定向，单独给一个头
        url = 'https://authpay.jd.com/card/queryBindCard.action'
        headers =  {
            'Referer': 'https: // i.jd.com / user / info',
            'Upgrade - Insecure - Requests': '1',
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/63.0.3239.26 Safari/537.36 Core/1.63.5702.400 QQBrowser/10.2.1893.400'
        }
        try:
            resp = self.sess.get(url=url, headers=headers)
            if not response_status(resp):
                print(get_current_time(), '获取小白信用值错误')
                return
            else:
                wb_data = BeautifulSoup(resp.text, 'lxml')
                str_response = resp.text
                card_banks = re.findall('<span id=".*?" class="bank-logo">(.*?)</span>', str_response)
                card_nums = re.findall('<span class="tail-number">尾号(\d+)</span>', str_response)
                card_types = wb_data.find_all(attrs={'class':'type'})
                card_owners = re.findall('<span class="info">持卡人姓名：(.*?)</span>', str_response)
                card_phones = re.findall('<span class="info">手机号：(.*?)</span>', str_response)
                list_bank_card = []
                for card_bank, card_num, card_type, card_owner, card_phone in zip(card_banks,card_nums,
                                                       card_types,card_owners,card_phones):
                    dict_card_bank = {}
                    card_bank = card_bank
                    card_num = card_num
                    card_type = card_type.text.strip()
                    card_owner = card_owner
                    card_phone = card_phone
                    dict_card_bank['card_bank'] = card_bank
                    dict_card_bank['card_num'] = card_num
                    dict_card_bank['card_type'] = card_type
                    dict_card_bank['card_owner'] = card_owner
                    dict_card_bank['card_phone'] = card_phone
                    list_bank_card.append(dict_card_bank)
                self.info_dict['card_info'] = list_bank_card
        except Exception as e:
            print(get_current_time(), e)
        return
    #常用收货地址信息
    def get_order_address(self):
        url = 'https://easybuy.jd.com/address/getEasyBuyList.action'
        self.headers['Host'] = 'easybuy.jd.com'
        self.headers['Referer'] = 'https://i.jd.com/user/info'
        try:
            resp = self.sess.get(url=url, headers=self.headers)
            if not response_status(resp):
                print(get_current_time(), '获取小白信用值错误')
                return
            else:
                wb_data = BeautifulSoup(resp.text, 'lxml')
                items = wb_data.driverect('div.item-lcol')
                list_dict_address = []
                for item in items:
                    dict_address_info = {}
                    fields = item.driverect('div.fl')
                    name = fields[0].text
                    area = fields[1].text
                    address = area + fields[2].text.replace(' ','')
                    phone = fields[3].text
                    mail = fields[5].text

                    dict_address_info['name'] = re.sub('[\r\n\t'']','', name).lstrip()
                    dict_address_info['area'] = re.sub('[\r\n\t]','', area).lstrip()
                    dict_address_info['address'] = re.sub('[\r\n\t]','', address).lstrip()
                    dict_address_info['phone'] = re.sub('[\r\n\t]','', phone).lstrip()
                    dict_address_info['mail'] = re.sub('[\r\n\t]','', mail).lstrip()
                    list_dict_address.append(dict_address_info)
                self.info_dict['address_info'] = list_dict_address
        except Exception as e:
            print(get_current_time(), e)
        return

    def get_order_info(self, unpaid=False):
        url = 'https://order.jd.com/center/list.action'
        #近一年的订单详情
        list_payload = []
        payload_1 = {
            'search': 0,
            'd': 2,
            's': 4096,
        }
        year = int(datetime.datetime.now().year) - 1

        payload_2 = {
            'search': 0,
            'd': year,
            's': 4096,
        }
        list_payload.append(payload_1)
        list_payload.append(payload_2)
        self.headers['Host'] = 'order.jd.com'
        self.headers['Referer'] = 'https://passport.jd.com/uc/login?ltype=logout'
        try:
            list_order_info = []
            for payload in list_payload:
                resp = self.sess.get(url=url, params=payload, headers=self.headers)
                if not response_status(resp):
                    print(get_current_time(), '获取订单页信息失败')
                    return
                else:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    order_table = soup.find('table', {'class': 'order-tb'})
                    table_bodies = order_table.driverect('tbody')


                    for table_body in table_bodies:
                        dict_order_info = {}
                        # get deal_time, order_id
                        tr_th = table_body.driverect('tr.tr-th')[0]
                        deal_time = get_tag_value(tr_th.driverect('span.dealtime'))
                        order_id = get_tag_value(tr_th.driverect('span.number a'))

                        # get sum_price, pay_method
                        amount_div = table_body.find('div', {'class': 'amount'})
                        sum_price = ''
                        if amount_div:
                            spans = amount_div.driverect('span')
                            wait_payment = bool(table_body.driverect('a.btn-pay'))
                            # if the order is waiting for payment, the price after the discount is shown.
                            if wait_payment:
                                sum_price = get_tag_value(amount_div.driverect('strong'), index=1)[1:]
                            else:
                                sum_price = get_tag_value(spans, index=0)[4:]

                        # get order status
                        order_status = get_tag_value(table_body.driverect('span.order-status'))
                        order_status = str(order_status).strip('订单状态：')
                        if order_status == '已取消':
                            continue
                        # get name and quantity of items in order
                        items_dict = dict()  # {'item_id_1': quantity_1, 'item_id_2': quantity_2, ...}
                        tr_bds = table_body.driverect('tr.tr-bd')
                        for tr_bd in tr_bds:
                            item = tr_bd.find('div', {'class': 'goods-item'})
                            if not item:
                                break
                            item_id = item.get('class')[1][2:]
                            quantity = get_tag_value(tr_bd.driverect('div.goods-number'))[1:]
                            items_dict['item_id'] = item_id
                            items_dict['item_quantity'] = quantity
                        consignee_info = table_body.driverect('div.pc')
                        if consignee_info:
                            consignee_info = consignee_info[0]
                            consignee = re.search('<strong>(.*?)</strong>', str(consignee_info)).group(1)
                            consignee_address = re.findall('<p>(.*?)</p>', str(consignee_info))[0]
                            consignee_phone = re.findall('<p>(.*?)</p>', str(consignee_info))[1]
                        else:
                            consignee = ''
                            consignee_address = ''
                            consignee_phone = ''
                        dict_order_info['order_id'] = order_id
                        dict_order_info['deal_time'] = deal_time
                        dict_order_info['item_id'] = items_dict.get('item_id', 1556589)
                        dict_order_info['item_quantity'] = items_dict.get('item_quantity', 1)
                        dict_order_info['order_status'] = order_status
                        dict_order_info['sum_price'] = sum_price
                        dict_order_info['consignee'] = consignee
                        dict_order_info['consignee_address'] = consignee_address
                        dict_order_info['consignee_phone'] = consignee_phone
                        list_order_info.append(dict_order_info)
            self.info_dict['order_info'] = list_order_info
        except Exception:
            print(get_current_time(), traceback.format_exc())
    def inser_mongo(self):
        _id = '4' + '-' + str(uuid.uuid4())
        self.info_dict['_id'] = _id
        self.info_dict['id'] = dict_id['JD']
        self.info_dict['is_new'] = True
        self.consume_info.insert(self.info_dict)
def main():
    asst = JD()
    asst.login_by_username()
    asst.get_jd_credit()
    asst.get_bai_score()
    asst.get_card_info()
    asst.get_order_address()
    asst.get_order_info()
    asst.get_order_info()
    asst.inser_mongo()
if __name__ == '__main__':
    main()