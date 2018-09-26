"""
@date : 20180829
@author : payne
@upload_to_mysql
"""

from Config.config import *
import time
import json
from Database.mysql import *
import logging
from tools.jd_tools import get_current_time
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')
logger = logging.getLogger()


# 运营商信息同步至mysql
class upload_mysql_operator(object):
    def __init__(self):
        super(upload_mysql_operator, self).__init__()
        self.time_now = int(time.time())
        self.call_num_list = []
        self.night_call_list = []
        self.silent_day_list = []
        self.month_fee_list = []
        self.call_duration_list = []
        self.calling_list = []
        self.called_list = []
        self.calling_duration_list = []
        self.called_duration_list = []
    def data_combine(self):
        target_collection = mongo_connect()['operator_info']
        data_list = list(target_collection.find({'id':{'$in':[1,2]}, 'is_new':True}))
        if data_list:
            for data in data_list:
                id = data['id']
                _id = data['_id']
                regis_name = data['regis_name']
                regis_id = int(data['regis_id'])
                regis_address = data['regis_address']
                regis_date = data['regis_date']
                month_basic_fee = data['month_basic_fee']
                # 单位:天
                number_duration = (self.time_now - int(regis_date))/86400
                month_info_list = []
                #手机通话地区信息
                call_area_infos = call_area_info(data)
                #手机消费信息
                month_consumes = month_consume(data)
                #Top5高频联系人
                top_5_persons = top_5_call_person(data)
                #Top5通话时长
                top_5_duration_persons = top_5_duration_person(data)
                #全部通话信息
                all_call_infos = all_call_info(data)
                for each_month_call in data['call_info']:
                    month_fee = each_month_call['month_count']['month_fee']
                    month_fee = check_month_fee(month_fee, month_basic_fee)
                    self.month_fee_list.append(month_fee)
                    month = each_month_call['month']
                    call_times = len(each_month_call['call_info'])
                    dict_month_info = {}
                    for each_call in each_month_call['call_info']:
                        #通过电话的号码
                        call_num = each_call['call_num']
                        self.call_num_list.append(int(call_num))
                        call_time = each_call['call_time']
                        night_call = check_night_call(call_time)
                        self.night_call_list.append(night_call)
                        call_date = each_call['call_date']
                        silent_day = check_silent(call_date)
                        self.silent_day_list.append(silent_day)
                        call_duration = each_call['call_duration']

                        if call_duration !=' ':
                            self.call_duration_list.append(float(call_duration))
                        call_type = each_call['call_type']
                        if call_type == '主叫':
                            self.calling_list.append(True)
                            if call_duration != ' ':
                                self.calling_duration_list.append(call_duration)
                        else:
                            self.called_list.append(False)
                            if call_duration != ' ':
                                self.called_duration_list.append(call_duration)
                    #通话地区信息
                    dict_month_info['month'] = month
                    dict_month_info['call_times'] = call_times
                    dict_month_info['call_duration'] = sum(self.call_duration_list)
                    dict_month_info['called_times'] = len(self.called_list)
                    dict_month_info['called_duration'] = sum(self.called_duration_list)
                    dict_month_info['calling_times'] = len(self.calling_list)
                    dict_month_info['calling_duration'] =sum(self.calling_duration_list)
                    dict_month_info['month_fee'] = month_fee
                    dict_month_info['month_basic_fee'] = float(month_basic_fee)
                    json_month_info = json.dumps(dict_month_info, ensure_ascii=False)
                    month_info_list.append(json_month_info)
                total_night_call = self.night_call_list.count(True)
                total_call_num = len(self.call_num_list)

                #最近10天静默天数
                recent_silent_day = recent_silent(self.silent_day_list[-10:])
                ave_month_fee = average(self.month_fee_list)
                last_month_fee = self.month_fee_list[-1]
                special_call = special_numbers(self.call_num_list)
                data = (id, regis_id, regis_name, regis_address,regis_date, total_call_num, number_duration,
                              total_night_call, 0, 0, recent_silent_day, ave_month_fee, last_month_fee,
                              special_call, month_consumes, call_area_infos, top_5_duration_persons, top_5_persons,
                              all_call_infos)
                #同步数据至mysql
                insert_opertor_sql(data)

                #更新is_new为True, 防止重复同步
                target_collection.update_one({'_id':_id}, {'$set':{'is_new':False}})
                return


# 电商网站消费信息 同步至mysql
class upload_mysql_consume(object):
    def __init__(self):
        super(upload_mysql_consume, self).__init__()
        pass
    def data_combine(self):
        target_collection = mongo_connect()['consume_info']
        data_list = list(target_collection.find({'id': {'$in':[4,5]}, 'is_new': True}))
        if data_list:
            for data in data_list:
                source = data['id']
                _id = data['_id']
                name = ' '
                regis_num = 0
                bai_tiao = data['credit_status']
                balanced = data['balanced']
                bai_score = data['bai_score']
                card_info = json.dumps(dict(zip(range(len(data['order_info'])), data['order_info'])), ensure_ascii=False)
                address_info = json.dumps(dict(zip(range(len(data['address_info'])), data['address_info'])), ensure_ascii=False)
                order_info = get_orders_info(data['order_info'])
                total_orders = order_info['total_orders']
                order_amount = order_info['order_amount']
                single_highest = order_info['single_highest']
                ave_amonut = order_info['ave_amonut']
                item_quantities = order_info['item_quantities']
                month_order = get_month_consume(data['order_info'])
                address_order = get_address_order(data)

                data = (source, name, regis_num, bai_tiao, balanced, bai_score, card_info,
                        address_info, total_orders, order_amount, single_highest, ave_amonut,
                        item_quantities, month_order, address_order)
                # 同步数据至mysql
                insert_buy_sql(data)
                # 更新is_new为True, 防止重复同步
                target_collection.update_one({'_id': _id}, {'$set': {'is_new': False}})
                return


#--------------------------------------------------------QQ通讯录--------------------------------------------------------

class upload_mysql_QQIC(object):
    def __init__(self):
        super(upload_mysql_QQIC, self).__init__()
        pass
    def upload(self):
        target_collection = mongo_connect()['credit_info.QQIC']
        data_list = list(target_collection.find({'id': {'$in': [9]}, 'is_new': True}))
        print(data_list)
        if data_list:
            for data in data_list:
                source = data['id']
                _id = data['_id']
                uname = data['number']
                captcha = data['captcha']
                list_contact = []
                for each in data['contact']:
                    dict_contact = {}
                    name = each['name']
                    number = each['number']
                    dict_contact['name'] = name
                    dict_contact['number'] = number
                    list_contact.append(dict_contact)
                contact = json.dumps(dict(zip(range(len(list_contact)), list_contact)), ensure_ascii=False)

                data = (source, uname, contact, captcha)
                print(data)
                # 同步数据至mysql
                insert_QQIC_sql(data)
                # 更新is_new为True, 防止重复同步
                target_collection.update_one({'_id': _id}, {'$set': {'is_new': False}})
                return


#----------------------------------------------------------今借到--------------------------------------------------------

class upload_mysql_jjd(object):
    def __init__(self):
        super(upload_mysql_jjd, self).__init__()
        pass
    def upload(self):
        target_collection = mongo_connect()['JJD']
        data_list = list(target_collection.find({'id': {'$in': [7]}, 'is_new': True}))

        if data_list:
            for data in data_list:
                list_need_2_pay = []
                list_amount = []
                list_instant_pay = []
                list_people = []
                info_dict = {}
                source = data['id']
                _id = data['_id']
                uname = data['name']
                number = data['number']
                borrow_count = data['borrow']['borrow_count']
                total_interest = data['borrow']['fee']
                balance = data['wallet_info']['balance']
                list_contact = []
                for each in data['borrow']['borrow']:
                    dict_borrow = {}
                    received_time = each['received_time']
                    borrower_name = each['borrow_name']
                    borrow_amount = each['borrow_amount']
                    lender_name = each['lender_name']
                    service_fee = each['service_fee']
                    need_2_pay = each['need_2_pay']
                    if float(need_2_pay) != 0:
                        service_fee = float(need_2_pay) - float(borrow_amount)
                    paid = 0
                    status = each['status']
                    borrow_type = each['borrow_type']
                    borrow_date = each['borrow_date']
                    pay_type = each['pay_type']
                    pay_date = each['pay_date']
                    interest = each['interest']
                    guarantee_fee = each['guarantee_fee']
                    purpose = each['purpose']
                    additional = each['additional']
                    if status == '未还清':
                        list_need_2_pay.append(need_2_pay)
                    list_amount.append(borrow_amount)
                    if borrow_date == pay_date:
                        list_instant_pay.append(borrow_amount)
                    list_people.append(lender_name)
                    dict_borrow['received_time'] = received_time
                    dict_borrow['borrower_name'] = borrower_name
                    dict_borrow['borrow_amount'] = borrow_amount
                    dict_borrow['lender_name'] = lender_name
                    dict_borrow['service_fee'] = service_fee
                    dict_borrow['need_2_pay'] = need_2_pay
                    dict_borrow['paid'] = paid
                    dict_borrow['status'] = status
                    dict_borrow['borrow_type'] = borrow_type
                    dict_borrow['borrow_date'] = borrow_date
                    dict_borrow['pay_type'] = pay_type
                    dict_borrow['pay_date'] = pay_date
                    dict_borrow['interest'] = interest
                    dict_borrow['guarantee_fee'] = guarantee_fee
                    dict_borrow['purpose'] = purpose
                    dict_borrow['additional'] = additional
                    list_contact.append(dict_borrow)
                json_data = json.dumps(dict(zip(range(len(list_contact)), list_contact)), ensure_ascii=False)

                source= source
                name = uname
                number = number
                balance = balance
                need_2_pay = sum(list_need_2_pay)
                total_amount = sum(list_amount)
                max_amount = max(list_amount)
                count = len(list_amount)
                count_people = len(list(set(list_people)))
                instant_pay_rate = len(list_instant_pay) / len(list_amount)
                borrow = json_data
                max_need_2_pay = max(list_need_2_pay)
                interest_2_pay = total_interest
                borrow_times = borrow_count

                data = (source, name, number, balance, need_2_pay,total_amount,max_amount,count,count_people,
                        instant_pay_rate,borrow,max_need_2_pay,interest_2_pay,borrow_times)
                print(data)
                # 同步数据至mysql
                insert_JJD_sql(data)
                # 更新is_new为True, 防止重复同步
                target_collection.update_one({'_id': _id}, {'$set': {'is_new': False}})
                return

#----------------------------------------------------------无忧借贷--------------------------------------------------------

class upload_mysql_wyjd(object):
    def __init__(self):
        super(upload_mysql_wyjd, self).__init__()
        pass
    def upload(self):
        target_collection = mongo_connect()['WYJD']
        data_list = list(target_collection.find({'id': {'$in': [7, 10]}, 'is_new': True}))
        if data_list:
            for data in data_list:
                if not data:
                    logger.error(str(get_current_time(), 'upload_mysql_wyjd  no data'))
                list_need_2_pay = []
                list_amount = []
                list_instant_pay = []
                list_people = []
                source = data['id']
                _id = data['_id']
                uname = data['common_data']['name']
                number = data['common_data']['phone']
                borrow_count = len(data['borrow'])
                total_interest = 0
                balance = data['common_data']['current_money']
                total_need_2_pay = data['common_data']['wait_repay']
                list_contact = []
                for each in data['borrow']:
                    dict_borrow = {}
                    received_time = each['date']
                    borrower_name = uname
                    borrow_amount = each['amount']
                    lender_name = each['loaner']
                    service_fee = 0
                    need_2_pay = float(borrow_amount) + float(service_fee)
                    if float(need_2_pay) != 0:
                        service_fee = float(need_2_pay) - float(borrow_amount)
                    paid = 0
                    status = each['loan_status'].split(';')[0]
                    borrow_type = ''
                    borrow_date = each['date']
                    pay_type = '等额本息'
                    if status == '已完成':
                        pay_date = each['date']
                        received_time = ''
                        borrow_date = ''
                    else:
                        pay_date = ''
                    interest = each['interest']
                    guarantee_fee = ''
                    purpose = ''
                    additional = ''
                    if status != '已完成':
                        list_need_2_pay.append(need_2_pay)
                    list_amount.append(float(borrow_amount))
                    if borrow_date == pay_date:
                        list_instant_pay.append(float(borrow_amount))
                    list_people.append(lender_name)
                    dict_borrow['received_time'] = received_time
                    dict_borrow['borrower_name'] = borrower_name
                    dict_borrow['borrow_amount'] = float(borrow_amount)
                    dict_borrow['lender_name'] = lender_name
                    dict_borrow['service_fee'] = service_fee
                    dict_borrow['need_2_pay'] = need_2_pay
                    dict_borrow['paid'] = paid
                    dict_borrow['status'] = status
                    dict_borrow['borrow_type'] = borrow_type
                    dict_borrow['borrow_date'] = borrow_date
                    dict_borrow['pay_type'] = pay_type
                    dict_borrow['pay_date'] = pay_date
                    dict_borrow['interest'] = interest
                    dict_borrow['guarantee_fee'] = guarantee_fee
                    dict_borrow['purpose'] = purpose
                    dict_borrow['additional'] = additional
                    list_contact.append(dict_borrow)
                json_data = json.dumps(dict(zip(range(len(list_contact)), list_contact)), ensure_ascii=False)

                source= source
                name = uname
                number = int(number)
                balance = balance
                need_2_pay = total_need_2_pay
                total_amount = sum(list_amount)
                max_amount = max(list_amount)
                count = len(list_amount)
                count_people = len(list(set(list_people)))
                instant_pay_rate = len(list_instant_pay) / len(list_amount)
                borrow = json_data
                max_need_2_pay = max(list_need_2_pay)
                interest_2_pay = total_interest
                borrow_times = borrow_count
                data = (source, name, number, balance, need_2_pay,total_amount,max_amount,count,count_people,
                        instant_pay_rate,borrow,max_need_2_pay,interest_2_pay,borrow_times)
                print(data)
                # 同步数据至mysql
                insert_JJD_sql(data)
                # 更新is_new为True, 防止重复同步
                target_collection.update_one({'_id': _id}, {'$set': {'is_new': False}})
                return

if __name__ == '__main__':
    init = upload_mysql_wyjd()
    init.upload()