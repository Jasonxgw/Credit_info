# -*- coding: UTF-8 -*-
"""
@date : 2018.9.10
@author : payne
@Func: 今借到主函数
"""
import uuid
from Config.config import *
import datetime
import pickle
from bs4 import BeautifulSoup
from tools.jd_tools import *
import traceback
import json
import logging
import sys

# 日志基本配置(同时写入到文件和输出到控制台)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')
logger = logging.getLogger()

#今借到登录地址, post登录
login_url = 'https://www.gushistory.com/jjdApi/user/login4WX?'

class JJD(object):
    def __init__(self, unam, upasswd):
        self.username = ''
        self.nick_name = unam + str(uuid.uuid4())
        self.is_login = False
        self.risk_control = ''
        self.item_cat = dict()
        self.uname = unam
        self.upasswd = upasswd
        self.headers = {
                'Host': 'www.gushistory.com',
                'Connection': 'keep-alive',
                'Content-Length': '235',
                'Origin': 'https://www.gushistory.com',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 5.1.1; SM-G935F Build/LMY48Z) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Version/4.0 Chrome/39.0.0.0 Safari/537.36 MicroMessenger/6.6.7.1321(0x26060736) NetType/WIFI Language/zh_CN',
                'Content-Type': 'application/json',
                'Accept': '*/*',
                'Referer': 'https://www.gushistory.com/jjd2/html/register/login.html',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,en-US;q=0.8',
                'X-Requested-With': 'com.tencent.mm'
}
        self.debit = mongo_connect()['JJD']
        self.info_dict = {}
        self.sess = requests.session()


    # def _load_cookies(self):
    #     cookies_file = ''
    #     for name in os.listdir('./cookies'):
    #         if name.endswith('.cookies'):
    #             cookies_file = './cookies/{0}'.format(name)
    #             break
    #     with open(cookies_file, 'rb') as f:
    #         local_cookies = pickle.load(f)
    #     self.sess.cookies.update(local_cookies)
    #     self.is_login = self._validate_cookies()
    # def _save_cookies(self):
    #     cookies_file = './cookies/{0}.cookies'.format(self.nick_name)
    #     directory = os.path.dirname(cookies_file)
    #     if not os.path.exists(directory):
    #         os.makedirs(directory)
    #     with open(cookies_file, 'wb') as f:
    #         pickle.dump(self.sess.cookies, f)
    #
    # def _validate_cookies(self):  # True -- cookies is valid, False -- cookies is invalid
    #     passwd = md5(md5(self.upasswd))
    #     payload = {"c_telephone": "18645145512",
    #                "c_pwd": passwd,
    #                "c_head": "http://thirdwx.qlogo.cn/mmopen/5FmQOwXZHibbC0mic6TAIibGVTpCkTeOVo30giaRIX3Irjks23jKgKibCBhm18Ws4FKk"
    #                          "Owp6SO9fBf61c1t8Sdz9STA4IcANGcqxk/132",
    #                "c_open_id": "ocqQKt3G5aPltaDt6usRewv7XQFo"
    #                }
    #     response = self.sess.post(url=login_url, data=json.dumps(payload), headers=self.headers, verify=False,
    #                               allow_redirects=False)
    #     json_Data = json.loads(response.text)
    #     if json_Data:
    #         status_code = json_Data['code']
    #         if status_code == 200:
    #             return json_Data
    #         else:
    #             return False
    #     else:
    #         return False

    def login(self):
        #今借到输入密码以后用MD5加密两次
        passwd = md5(md5(self.upasswd))
        payload = {"c_telephone":self.uname,
                    "c_pwd":passwd,
                    "c_head": "http://thirdwx.qlogo.cn/mmopen/5FmQOwXZHibbC0mic6TAIibGVTpCkTeOVo30giaRIX3Irjks23jKgKibCBhm18Ws4FKk"
                              "Owp6SO9fBf61c1t8Sdz9STA4IcANGcqxk/132",
                    "c_open_id": "ocqQKt3G5aPltaDt6usRewv7XQFo"
        }
        response = self.sess.post(url=login_url, data=json.dumps(payload), headers=self.headers, verify=False)
        json_data = json.loads(response.text)
        if json_data['code'] == 200:
            logger.info('登陆成功')
            self.get_common_data(json_data)
            return json_data

        else:
            logger.error('账户或密码错误, 请重试')
            sys.exit(0)
    def get_common_data(self, data):
        target = data['object']
        name = target['c_user_name']
        address = target['c_home_addr']
        phone = target['telephone']
        num_borrow = target['n_borrow_cnt']
        num_guarantee = target['n_guarantee_cnt']
        self.jjd_token = target['token']
        self.info_dict['name'] = name
        self.info_dict['address'] = address
        self.info_dict['phone'] = phone
        self.info_dict['num_borrow'] = num_borrow
        self.info_dict['num_guarantee'] = num_guarantee
        return
    def get_wallet_info(self):
        dict_wallet_info = {}
        list_wallet_info = []
        url = 'https://www.gushistory.com/jjdApi/my/getMyAccountList2?'
        self.headers.update({'Referer':'https://www.gushistory.com/jjd2/html/my/wallet.html'})
        data = {
            'start':0,
            'limit':100,
            'filter':[]
        }
        payload = {
            'token':self.jjd_token
        }
        response = self.sess.post(url=url, data=json.dumps(data), params= payload, headers=self.headers)
        if response.status_code == 200:
            data = json.loads(response.text)['object']
            wallet_balance = data['n_amt']
            total_count = data['n_total_cnt']
            for each_data in data['l_account_list']:
                dict_account = {}
                id = each_data['id']
                beneficiary_num = each_data['t_send_tm']
                beneficiary_name = each_data['c_user_name']
                date = each_data['c_tm']
                amount = each_data['n_amt']
                type = each_data['c_type']
                dict_account['id'] = id
                dict_account['beneficiary_num'] = beneficiary_num
                dict_account['beneficiary_name'] = beneficiary_name
                dict_account['type'] = type
                dict_account['date'] = date
                dict_account['amount'] = amount
                list_wallet_info.append(dict_account)
            dict_wallet_info['account'] = list_wallet_info
            dict_wallet_info['balance'] = wallet_balance
            dict_wallet_info['total_count'] = total_count
            self.info_dict['wallet_info'] = dict_wallet_info
            return
    def borrow(self):
        url = 'https://www.gushistory.com/jjdApi/my/getBorrowAccount2?'
        self.headers.update({'Referer': 'https://www.gushistory.com/jjd2/html/my/borrowList.html'})
        data = {
            'start': 0,
            'limit': 100,
        }
        payload = {
            'token': self.jjd_token
        }
        response = self.sess.post(url=url, data=json.dumps(data), params=payload, headers=self.headers)
        if response.status_code ==200:
            json_data = json.loads(response.text)['object']
            dict_borrow = {}
            list_borrow = []
            borrow_count = json_data['n_lend_count']
            repay_max = json_data['n_history_repay_max']
            fee = json_data['n_fee_amt']
            dict_borrow['borrow_count'] = borrow_count
            dict_borrow['repay_max'] = repay_max
            dict_borrow['fee'] = fee
            self.headers.pop('Content-Length')
            for each_data in json_data['l_lend_list']:
                dict_each_borrow = {}
                iouid = each_data['c_iou_id']
                base_url = 'https://www.gushistory.com/jjdApi/iou/getIOU?'
                referer = 'https://www.gushistory.com/jjd2/html/center/outIOUDetail.html?iouid={}'.format(iouid)
                self.headers.update({'Referer': referer})
                timestamp = int(time.time()) * 1000
                token = self.jjd_token
                detail_url = base_url + 'iouid=' + str(iouid) + '&token=' + str(token) + '&timestamp=' + str(timestamp)
                res = self.sess.get(url=detail_url, headers=self.headers)
                if res.status_code == 200:
                    detail_data = json.loads(res.text)['object']
                    borrow_date = detail_data['t_borrow_tm']
                    borrow_name = detail_data['c_borrower_name']
                    borrow_amount = detail_data['n_now_amt']
                    lender_name = detail_data['c_lender_name']
                    need_2_pay = detail_data['n_total_amt']
                    status = detail_data['n_status']
                    if int(status) == 3:
                        status = '已还清'
                    else:
                        status = '未还清'
                    borrow_type = '线上'
                    received_time = detail_data['t_crt_tm']
                    pay_type = '等额本息'
                    pay_date = detail_data['t_repay_tm']
                    interest = detail_data['n_interest_rate']
                    service_fee = detail_data['n_to_repay_amt']
                    guarantee_fee = detail_data['n_guarantee_amt']
                    purpose = detail_data['c_purpose']
                    additional = ' '
                    dict_each_borrow['borrow_date'] = borrow_date
                    dict_each_borrow['borrow_name'] = borrow_name
                    dict_each_borrow['borrow_amount'] = borrow_amount
                    dict_each_borrow['lender_name'] = lender_name
                    dict_each_borrow['need_2_pay'] = need_2_pay
                    dict_each_borrow['status'] = status
                    dict_each_borrow['borrow_type'] = borrow_type
                    dict_each_borrow['received_time'] = received_time
                    dict_each_borrow['pay_type'] = pay_type
                    dict_each_borrow['pay_date'] = pay_date
                    dict_each_borrow['interest'] = interest
                    dict_each_borrow['service_fee'] = service_fee
                    dict_each_borrow['guarantee_fee'] = guarantee_fee
                    dict_each_borrow['purpose'] = purpose
                    dict_each_borrow['additional'] = additional
                    list_borrow.append(dict_each_borrow)
            dict_borrow['borrow'] = list_borrow
            self.info_dict['borrow'] = dict_borrow
        else:
            self.info_dict['dict_borrow'] = {}
        return
    def inser_mongo(self):
        _id = '7' + '-' + str(uuid.uuid4())
        self.info_dict['_id'] = _id
        self.info_dict['id'] = dict_id['JinJieDao']
        self.info_dict['is_new'] = True
        self.info_dict['number'] = self.uname
        self.debit.insert(self.info_dict)

    def lend(self):
        url = 'https://www.gushistory.com/jjdApi/my/getLendAccount2?token=jjd_20B74E4DF641D8845C81D7A36AA11D0A'
        self.headers.update({'Referer': 'https://www.gushistory.com/jjd2/html/my/lendList.html'})
        data = {
            'start': 0,
            'limit': 100,
        }
        payload = {
            'token': self.jjd_token
        }
        response = self.sess.post(url=url, data=json.dumps(data), params=payload, headers=self.headers)
        if response.status_code == 200:
            return
    def guarantee(self):
        base_url = 'https://www.gushistory.com/jjdApi/my/getGuaranteeAccount?'
        self.headers.update({'Referer': 'https://www.gushistory.com/jjd2/html/my/guaranteeList.html', })
        timestamp = int(time.time()) * 1000
        token = self.jjd_token
        detail_url = base_url + 'token=' + str(token) + '&timestamp=' + str(timestamp)
        self.headers.pop('Content-Length')
        res = self.sess.get(url=detail_url, headers=self.headers)
        if res.status_code == 200:
            return


if __name__ == '__main__':
    logger.info('请输入账户: ')
    uname = input()
    logger.info('请输入密码: ')
    upasswd = input()
    init = JJD(uname,upasswd)
    init.login()
    init.get_wallet_info()
    init.borrow()
    init.inser_mongo()


