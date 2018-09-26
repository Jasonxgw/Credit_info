# -*- coding:utf-8 -*-
"""
@author : payne
@date : 20180824
@config
"""
import os
import random
import datetime
import re
import time
from dateutil.relativedelta import relativedelta
import pymongo
import pymysql
import json

# 一些配置变量
dict_id = {
    'China_Unicom':1,
    'China_Telecom':2,
    'China_Mobile':3,
    'JD':4,
    'TaoBao':5,
    'ZhiFuBao':6,
    'JinJieDao':7,
    'YouPingZheng':8,
    'QQTongXunLu':9,
    'WYJD':10

}
#京东白条开通状态
dict_jd_credit = {
    3 : '开通',
    2 : '未开通'
}
# selenium 自动输出文字
def slow_input(ele, word):
    for i in word:
        # 输出一个字符
        ele.send_keys(i)
        # 随机睡眠0到1秒
        time.sleep(random.uniform(0, 0.5))

list_special_numbers = [110, 120, 119, 112, 12315]

def mongo_connect():
    client = pymongo.MongoClient('localhost', 27017)
    credit_info = client['credit_info']
    return credit_info

def mysql_connect():
    conn = pymysql.connect('localhost', user='root', password='Panny2601039', db='operator_info', port=3306)
    return conn
def get_month(datetime):
    if datetime:
        month = re.search('2\d+-(\d+)-\d+', str(datetime)).group(1)
        return month
    else:
        print('datetime format error')


# -*- coding: UTF-8 -*-
"""
Created on 2017年10月23日
@author: Leo
"""

# 系统内部库
import math
import time
import datetime

# 第三方库
from dateutil.relativedelta import relativedelta


class TimeUtil:
    def __init__(self):
        # 初始化一些日期,时间和时间模板常量
        self.Monday = "周一"
        self.Tuesday = "周二"
        self.Wednesday = "周三"
        self.Thursday = "周四"
        self.Friday = "周五"
        self.Saturday = "周六"
        self.Sunday = "周日"

        self.Morning = "上午"
        self.Afternoon = "下午"
        self.Evening = "晚上"
        self.Midnight = "半夜"

        self.morning_start = "060000"
        self.afternoon_start = "120000"
        self.evening_start = "180000"
        self.evening_end = "235959"
        self.midnight_start = "000000"

        self.time_hms_layout = "%H%M%S"
        self.time_ymd_layout = "%Y%M%D"

    # 获取周几
    def get_week_day(self, date):
        week_day_dict = {
            0: self.Monday,
            1: self.Tuesday,
            2: self.Wednesday,
            3: self.Thursday,
            4: self.Friday,
            5: self.Saturday,
            6: self.Sunday,
        }
        day = date.weekday()
        return week_day_dict[day]

    # 计算日期时间差
    @staticmethod
    def get_time_gap(time_start, time_end):
        start_time_year = int(time_start.split("-")[0])
        start_time_month = int(time_start.split("-")[1])
        start_time_day = int(time_start.split("-")[2])

        end_time_year = int(time_end.split("-")[0])
        end_time_month = int(time_end.split("-")[1])
        end_time_day = int(time_end.split("-")[2])

        return datetime.datetime(end_time_year, end_time_month, end_time_day) - \
               datetime.datetime(start_time_year, start_time_month, start_time_day)

    # 计算最大周数
    @staticmethod
    def get_max_week_num(gap):
        if gap >= 0:
            if gap != 0:
                return math.ceil(float(gap / 7))
            else:
                return 0
        else:
            raise ValueError("No time gap or gap is error!")

    # 时间转换为上午,下午,晚上和半夜
    def _divide_time_quantum(self, time_hms, first_time, second_time):
        try:
            if int(time.strftime(self.time_hms_layout, first_time)) <= \
                    int(time.strftime(self.time_hms_layout, time_hms)) < \
                    int(time.strftime(self.time_hms_layout, second_time)):
                return True
            else:
                return False
        except Exception as err:
            print(err.with_traceback(err))

    # 判断时间段
    def get_time_quantum(self, time_hms):
        if self._divide_time_quantum(time_hms=time.strptime(time_hms, self.time_hms_layout),
                                     first_time=time.strptime(self.morning_start, self.time_hms_layout),
                                     second_time=time.strptime(self.afternoon_start, self.time_hms_layout)) is True:
            return self.Morning

        elif self._divide_time_quantum(time_hms=time.strptime(time_hms, self.time_hms_layout),
                                       first_time=time.strptime(self.afternoon_start, self.time_hms_layout),
                                       second_time=time.strptime(self.evening_start, self.time_hms_layout)) is True:
            return self.Afternoon

        elif self._divide_time_quantum(time_hms=time.strptime(time_hms, self.time_hms_layout),
                                       first_time=time.strptime(self.evening_start, self.time_hms_layout),
                                       second_time=time.strptime(self.evening_end, self.time_hms_layout)) is True:
            return self.Evening

        elif self._divide_time_quantum(time_hms=time.strptime(time_hms, self.time_hms_layout),
                                       first_time=time.strptime(self.midnight_start, self.time_hms_layout),
                                       second_time=time.strptime(self.morning_start, self.time_hms_layout)) is True:
            return self.Midnight
        else:
            raise ValueError("Variable time_hms is illegal!")

    # 获取当前年月日的前几个月或者后几个月的时间
    @staticmethod
    def get_front_or_after_month(target_date=None, month=0,
                                 day=None, time_format_layout='%Y.%m.%d', timestamp=False):
        """
        :param target_date: str或者是date类型(格式通用,例),如果target_date为空,则默认日期为当天
        :param month: int类型的月份, int < 0 就是前面的月份, int > 0 就是后面的月份
        :param day: int类型的天数,计算后几天的,默认为空,如果不计算后几个月只计算后几天的,month=0即可
        :param time_format_layout: 日期格式化的模板,默认是%Y.%m.%d,输出是2017.11.01
        :param timestamp: 如果timestamp为True则返回时间戳
        :return: 返回target_date和计算完且格式化后的数据
        """
        # 判断目标日期的逻辑
        if target_date is None:
            _date = datetime.datetime.now()
        else:
            # 判断date的类型
            if isinstance(target_date, str):
                _date = datetime.datetime.strptime(target_date, "%Y-%m-%d")
            elif isinstance(target_date, datetime.datetime):
                _date = target_date
            else:
                raise ValueError("Parameter target_date is illegal!")
        _today = _date
        # 判断day的逻辑
        if day is not None:
            if isinstance(day, int):
                _delta = datetime.timedelta(days=int(day))
                _date = _date + _delta
            else:
                raise ValueError("Parameter day is illegal!")
        # 判断month的类型
        if isinstance(month, int):
            _result_date = _date + relativedelta(months=month)
            if timestamp:
                _result_date_ts = int(time.mktime(_result_date.timetuple())) * 1000
                _today_ts = int(time.mktime(_today.timetuple())) * 1000
                return _today_ts, _result_date_ts
            else:
                return _today.strftime(time_format_layout), _result_date.strftime(time_format_layout)
        else:
            raise ValueError("Month is not int,please confirm your variable`s type.")
def clean_data(data):
    cleaned_data = re.sub('[\r\t\n]','',data)
    cleaned_data = cleaned_data.strip()
    return cleaned_data

# 保存验证码
def save_image(resp, image_file):
    with open(image_file, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=1024):
            f.write(chunk)
#打开验证码
def open_image(image_file):
    if os.name == "nt":
        os.system('start ' + image_file)  # for Windows
    else:
        if os.uname()[0] == "Linux":
            os.system("eog " + image_file)  # for Linux
        else:
            os.system("open " + image_file)  # for Mac

#今借到密码加密
def md5(target):

    import hashlib
    h1 = hashlib.md5()
    h1.update(target.encode('utf8'))
    s2 = h1.hexdigest()
    return s2

# def check_

#获取最近6个月的月份，以供查询需要
def date_delta(open_date):
    list_date = []
    open_date = re.sub('[年月日]', '', str(open_date))
    month = datetime.datetime.now().month
    day = datetime.datetime.now().day
    year = datetime.datetime.now().year
    if len(str(day)) < 2:
        day = '0' + str(day)
    if len(str(month)) < 2:
        month = '0' + str(month)
    today = str(year) + str(month) + str(day)
    current_month_start = str(year) + str(month) + '01'
    current_month_end = str(year) + str(month) + str(day)
    list_date.append([current_month_start, current_month_end])
    #开户时间大于6个月
    if int(today) - int(open_date) >= 600:
        for i in range(5):
            delta = i + 1
            target = datetime.date.today() - relativedelta(months=+delta)
            last_month_start = re.search('2\d+-(\d+)-\d+', str(target)).group(1)
            query_year = re.search('(2\d+)-\d+-\d+', str(target)).group(1)
            this_month_start = str(query_year) + str(last_month_start) + '01'
            this_month_end = str(query_year) + str(last_month_start) + str(30)
            list_date.append([this_month_start, this_month_end])
    else:
        months = int(today) - int(open_date)
        #开户时间小于6个月
        if len(str(months)) >= 3:
            months = str(months)[1]
            for i in range(int(months)):
                delta = i + 1
                target = datetime.date.today() - relativedelta(months=+delta)
                last_month_start = re.search('2\d+-(\d+)-\d+', str(target)).group(1)
                query_year = re.search('(2\d+)-\d+-\d+', str(target)).group(1)
                this_month_start = str(query_year) + str(last_month_start) + '01'
                this_month_end = str(query_year) + str(last_month_start) + str(30)
                list_date.append([last_month_start, this_month_start, this_month_end])
    return list_date

#日期转时间戳
def date_to_timestamp(date:str):
    if '年' in date:
        date = str(date).replace('年', '-').replace('月', '-').replace('日', '')
        time_array = time.strptime(date, '%Y-%m-%d')
        time_stamp = int(time.mktime(time_array))
        return time_stamp
    elif '-' in date:
        time_array = time.strptime(date, '%Y-%m-%d %H:%M:%S')
        time_stamp = int(time.mktime(time_array))
        return time_stamp
    else:
        time_array = time.strptime(date, '%Y%m%d')
        time_stamp = int(time.mktime(time_array))
        return time_stamp


#分钟转秒
def minute_to_seconds(minute:str):
    if '分钟' in minute and '小时' not in  minute:
        minutes = minute.split('分钟')[0]
        seconds = minute.split('分钟')[1].strip('秒')
        total_seconds = int(minutes) * 60 + int(seconds)
        return total_seconds
    elif '分' in minute and '分钟' not in minute :
        minutes = minute.split('分')[0]
        seconds = minute.split('分')[1].strip('秒')
        total_seconds = int(minutes) * 60 + int(seconds)
        return total_seconds
    elif '小时' in  minute:
        hours = minute.split('小时')[0]
        minutes = minute.split('分钟')[0].split('小时')[1]
        seconds = minute.split('分钟')[1].strip('秒')
        total_seconds = int(hours) * 60 * 60 + int(minutes) * 60 + int(seconds)
        return total_seconds
    elif '分' in minute and '小时' in minute:
        hours = minute.split('小时')[0]
        minutes = minute.split('分')[0].split('小时')[1]
        seconds = minute.split('分')[1].strip('秒')
        total_seconds = int(hours) * 60 * 60 + int(minutes) * 60 + int(seconds)
        return total_seconds
    else:
        return ' '

def get_front_or_after_month(target_date=None, month=0,
                             day=None, time_format_layout='%Y.%m.%d', timestamp=False):
    """
    :param target_date: str或者是date类型(格式通用,例),如果target_date为空,则默认日期为当天
    :param month: int类型的月份, int < 0 就是前面的月份, int > 0 就是后面的月份
    :param day: int类型的天数,计算后几天的,默认为空,如果不计算后几个月只计算后几天的,month=0即可
    :param time_format_layout: 日期格式化的模板,默认是%Y.%m.%d,输出是2017.11.01
    :param timestamp: 如果timestamp为True则返回时间戳
    :return: 返回target_date和计算完且格式化后的数据
    """
    # 判断目标日期的逻辑
    if target_date is None:
        _date = datetime.datetime.now()
    else:
        # 判断date的类型
        if isinstance(target_date, str):
            _date = datetime.datetime.strptime(target_date, "%Y-%m-%d")
        elif isinstance(target_date, datetime.datetime):
            _date = target_date
        else:
            raise ValueError("Parameter target_date is illegal!")
    _today = _date
    # 判断day的逻辑
    if day is not None:
        if isinstance(day, int):
            _delta = datetime.timedelta(days=int(day))
            _date = _date + _delta
        else:
            raise ValueError("Parameter day is illegal!")
    # 判断month的类型
    if isinstance(month, int):
        _result_date = _date + relativedelta(months=month)
        if timestamp:
            _result_date_ts = int(time.mktime(_result_date.timetuple())) * 1000
            _today_ts = int(time.mktime(_today.timetuple())) * 1000
            return _today_ts, _result_date_ts
        else:
            return _today.strftime(time_format_layout), _result_date.strftime(time_format_layout)
    else:
        raise ValueError("Month is not int,please confirm your variable`s type.")

#判断是否夜间通话
def check_night_call(call_time):
    hour = re.search('\d+:(\d+):\d+', str(call_time)).group(1)
    night_hour = ['23', '24', '01', '02', '03', '04', '05', '06']
    if hour in night_hour:
        night_call = True
    else:
        night_call = False
    return night_call

#判断是否静默
def check_silent(call_date):
    #一个月中每一天
    days = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17',
            '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30']
    day = re.search('\d+-\d+-(\d+)', str(call_date)).group(1)
    if day in days:
        silent = False
    else:
        silent = True
    return silent

#最近静默天数
def recent_silent(days:list):
    list_temp = []
    for i in days:
        if i == True:
            list_temp.append(True)
    return len(list_temp)

#每月消费金额
def check_month_fee(fee, basic_fee):
    if float(fee) > float(basic_fee):
        fee = float(fee) + float(basic_fee)
    else:
        fee = float(basic_fee)
    return fee

#月平均消费金额
def average(numbers:list):
    average_fee = sum(numbers)/len(numbers)
    return average_fee

#特殊通话次数
def special_numbers(numbers:list):
    count = 0
    for each_number in numbers:
        if each_number in list_special_numbers:
            count += 1
    return count

# 手机通话地区信息
def call_area_info(data:dict):
    list_phone_info = []
    list_phone_area = []
    for each_month_call in data['call_info']:
        for each_call in each_month_call['call_info']:
            dict_phone_info = {}
            call_area = each_call['call_area']
            called_area = each_call['called_area']
            call_type = each_call['call_type']
            call_duration = each_call['call_duration']
            if call_type == '主叫':
                #本机通话地区
                list_phone_area.append(call_area)
                dict_phone_info['area'] = call_area
                dict_phone_info['call_duration'] = call_duration
                dict_phone_info['call_type'] = call_type
                list_phone_info.append(dict_phone_info)
            else:
                list_phone_area.append(called_area)
                dict_phone_info['area'] = called_area
                dict_phone_info['call_duration'] = call_duration
                dict_phone_info['call_type'] = call_type
                list_phone_info.append(dict_phone_info)
    areas = list(set(list_phone_area))
    list_dict_area_call = []
    for area in areas:
        dict_area_call = {}
        dict_area_call['area'] = area
        list_calling_duration = []
        list_called_duration = []
        for i in list_phone_info:
            if i['area'] == area:
                if i['call_type'] == '被叫':
                    if i['call_duration'] == ' ':
                        called_duration = 0
                    else:
                        called_duration = i['call_duration']
                    list_called_duration.append(called_duration)
                else:
                    if i['call_duration'] == ' ':
                        calling_duration = 0
                    else:
                        calling_duration = i['call_duration']
                    list_calling_duration.append(calling_duration)
        dict_area_call['calling_duration'] = list_calling_duration
        dict_area_call['called_duration'] = list_called_duration
        list_dict_area_call.append(dict_area_call)
    list_final_call_info = []
    for each in list_dict_area_call:
        dict_final_call_info = {}
        area = each['area']
        calling_times = len(each['calling_duration'])
        called_times = len(each['called_duration'])
        calling_durations = sum(each['calling_duration'])
        called_durations = sum(each['called_duration'])
        total_call_times = calling_times + called_times
        total_call_duration = calling_durations + called_durations
        dict_final_call_info['area'] = area
        dict_final_call_info['total_call_times'] = total_call_times
        dict_final_call_info['total_call_duration'] = total_call_duration
        dict_final_call_info['calling_times'] = calling_times
        dict_final_call_info['called_times'] = called_times
        dict_final_call_info['calling_durations'] = calling_durations
        dict_final_call_info['called_durations'] = called_durations

        list_final_call_info.append(dict_final_call_info)
    json_data = json.dumps(dict(zip(range(len(list_final_call_info)),list_final_call_info)), ensure_ascii=False)
    return json_data

def top_5_call_person(data:dict):
    list_phone_info = []
    list_phone_area = []
    list_phone_num = []
    list_call_date = []
    for each_month_call in data['call_info']:
        for each_call in each_month_call['call_info']:
            dict_phone_info = {}
            call_area = each_call['call_area']
            called_area = each_call['called_area']
            call_type = each_call['call_type']
            call_duration = each_call['call_duration']
            phone_num = each_call['call_num']
            call_date = each_call['call_date']
            list_call_date.append(call_date)
            list_phone_num.append(phone_num)
            if call_type == '主叫':
                list_phone_area.append(call_area)
                dict_phone_info['area'] = call_area
                dict_phone_info['call_duration'] = call_duration
                dict_phone_info['call_type'] = call_type
                dict_phone_info['phone_num'] = phone_num

                list_phone_info.append(dict_phone_info)
            else:
                list_phone_area.append(called_area)
                dict_phone_info['area'] = called_area
                dict_phone_info['call_duration'] = call_duration
                dict_phone_info['call_type'] = call_type
                dict_phone_info['phone_num'] = phone_num
                list_phone_info.append(dict_phone_info)
    numbers = list(set(list_phone_num))
    list_dict_area_call = []
    for number in numbers:
        dict_area_call = {}
        dict_area_call['number'] = number
        list_calling_duration = []
        list_called_duration = []

        for i in list_phone_info:
            if i['phone_num'] == number:
                if i['call_type'] == '被叫':
                    if i['call_duration'] == ' ':
                        called_duration = 0
                    else:
                        called_duration = i['call_duration']
                    list_called_duration.append(called_duration)
                else:
                    if i['call_duration'] == ' ':
                        calling_duration = 0
                    else:
                        calling_duration = i['call_duration']
                    list_calling_duration.append(calling_duration)
        dict_area_call['calling_duration'] = list_calling_duration
        dict_area_call['called_duration'] = list_called_duration


        list_dict_area_call.append(dict_area_call)

    list_final_call_info = []
    list_keys = []
    for each in list_dict_area_call:
        dict_final_call_info = {}
        area = list_phone_area[-1]
        phone_num = each['number']
        calling_times = len(each['calling_duration'])
        called_times = len(each['called_duration'])
        total_call_times = calling_times + called_times
        list_keys.append(total_call_times)
        dict_final_call_info['area'] = area
        dict_final_call_info['phone_num'] = phone_num
        dict_final_call_info['total_call_times'] = total_call_times
        dict_final_call_info['calling_times'] = calling_times
        dict_final_call_info['called_times'] = called_times

        dict_final_call_info['call_date'] = random.choice(list_call_date[:10])
        list_final_call_info.append(dict_final_call_info)
    temp = []
    Inf = 0
    for i in range(5):
        temp.append(list_keys.index(max(list_keys)))
        list_keys[list_keys.index(max(list_keys))] = Inf

    list_result = []
    for i in temp:
        list_result.append(list_final_call_info[i])

    key = range(len(list_result))
    json_data = json.dumps(dict(zip(key,list_result)), ensure_ascii=False)
    return json_data


def top_5_duration_person(data:dict):
    list_phone_info = []
    list_phone_area = []
    list_phone_num = []
    list_call_date = []
    for each_month_call in data['call_info']:
        for each_call in each_month_call['call_info']:
            dict_phone_info = {}
            call_area = each_call['call_area']
            called_area = each_call['called_area']
            call_type = each_call['call_type']
            call_duration = each_call['call_duration']
            phone_num = each_call['call_num']
            call_date = each_call['call_date']
            list_call_date.append(call_date)
            list_phone_num.append(phone_num)
            if call_type == '主叫':
                list_phone_area.append(call_area)
                dict_phone_info['area'] = call_area
                dict_phone_info['call_duration'] = call_duration
                dict_phone_info['call_type'] = call_type
                dict_phone_info['phone_num'] = phone_num

                list_phone_info.append(dict_phone_info)
            else:
                list_phone_area.append(called_area)
                dict_phone_info['area'] = called_area
                dict_phone_info['call_duration'] = call_duration
                dict_phone_info['call_type'] = call_type
                dict_phone_info['phone_num'] = phone_num
                list_phone_info.append(dict_phone_info)
    numbers = list(set(list_phone_num))
    list_dict_area_call = []
    for number in numbers:
        dict_area_call = {}
        dict_area_call['number'] = number
        list_calling_duration = []
        list_called_duration = []

        for i in list_phone_info:
            if i['phone_num'] == number:
                if i['call_type'] == '被叫':
                    if i['call_duration'] == ' ':
                        called_duration = 0
                    else:
                        called_duration = i['call_duration']
                    list_called_duration.append(called_duration)
                else:
                    if i['call_duration'] == ' ':
                        calling_duration = 0
                    else:
                        calling_duration = i['call_duration']
                    list_calling_duration.append(calling_duration)
        dict_area_call['calling_duration'] = list_calling_duration
        dict_area_call['called_duration'] = list_called_duration


        list_dict_area_call.append(dict_area_call)

    list_final_call_info = []
    list_keys = []
    for each in list_dict_area_call:
        dict_final_call_info = {}
        area = list_phone_area[-1]
        phone_num = each['number']
        calling_duration = sum(each['calling_duration'])
        called_duration = sum(each['called_duration'])
        total_call_duration = calling_duration + called_duration
        list_keys.append(total_call_duration)
        dict_final_call_info['area'] = area
        dict_final_call_info['phone_num'] = phone_num
        dict_final_call_info['total_call_duration'] = total_call_duration
        dict_final_call_info['calling_duration'] = calling_duration
        dict_final_call_info['called_duration'] = called_duration

        dict_final_call_info['call_date'] = random.choice(list_call_date[:10])
        list_final_call_info.append(dict_final_call_info)
    temp = []
    Inf = 0
    for i in range(5):
        temp.append(list_keys.index(max(list_keys)))
        list_keys[list_keys.index(max(list_keys))] = Inf

    list_result = []
    for i in temp:
        list_result.append(list_final_call_info[i])

    key = range(len(list_result))
    json_data = json.dumps(dict(zip(key,list_result)), ensure_ascii=False)
    return json_data

def all_call_info(data:dict):
    list_phone_info = []
    list_phone_area = []
    list_phone_num = []
    list_call_date = []
    for each_month_call in data['call_info']:
        for each_call in each_month_call['call_info']:
            dict_phone_info = {}
            call_area = each_call['call_area']
            called_area = each_call['called_area']
            call_type = each_call['call_type']
            call_duration = each_call['call_duration']
            phone_num = each_call['call_num']
            call_date = each_call['call_date']
            list_call_date.append(call_date)
            list_phone_num.append(phone_num)
            if call_type == '主叫':
                list_phone_area.append(call_area)
                dict_phone_info['area'] = call_area
                dict_phone_info['call_duration'] = call_duration
                dict_phone_info['call_type'] = call_type
                dict_phone_info['phone_num'] = phone_num

                list_phone_info.append(dict_phone_info)
            else:
                list_phone_area.append(called_area)
                dict_phone_info['area'] = called_area
                dict_phone_info['call_duration'] = call_duration
                dict_phone_info['call_type'] = call_type
                dict_phone_info['phone_num'] = phone_num
                list_phone_info.append(dict_phone_info)
    numbers = list(set(list_phone_num))
    list_dict_area_call = []
    for number in numbers:
        dict_area_call = {}
        dict_area_call['number'] = number
        list_calling_duration = []
        list_called_duration = []

        for i in list_phone_info:
            if i['phone_num'] == number:
                if i['call_type'] == '被叫':
                    if i['call_duration'] == ' ':
                        called_duration = 0
                    else:
                        called_duration = i['call_duration']
                    list_called_duration.append(called_duration)
                else:
                    if i['call_duration'] == ' ':
                        calling_duration = 0
                    else:
                        calling_duration = i['call_duration']

                    list_calling_duration.append(calling_duration)
        dict_area_call['calling_duration'] = list_calling_duration
        dict_area_call['called_duration'] = list_called_duration

        list_dict_area_call.append(dict_area_call)

    list_final_call_info = []
    list_keys = []
    for each in list_dict_area_call:
        dict_final_call_info = {}
        area = list_phone_area[-1]
        phone_num = each['number']
        calling_times = len(each['calling_duration'])
        called_times = len(each['called_duration'])
        calling_duration = sum(each['calling_duration'])
        called_duration = sum(each['called_duration'])
        total_call_times = calling_times + called_times
        list_keys.append(total_call_times)
        dict_final_call_info['area'] = area
        dict_final_call_info['phone_num'] = phone_num
        dict_final_call_info['total_call_times'] = total_call_times
        dict_final_call_info['calling_times'] = calling_times
        dict_final_call_info['called_times'] = called_times
        dict_final_call_info['calling_duration'] = calling_duration
        dict_final_call_info['called_duration'] = called_duration

        dict_final_call_info['total_call_times'] = calling_times + called_times
        dict_final_call_info['total_call_durations'] = calling_duration + called_duration

        dict_final_call_info['call_date'] = random.choice(list_call_date[:10])
        list_final_call_info.append(dict_final_call_info)
    keys = range(len(list_final_call_info))
    json_data = json.dumps(dict(zip(keys, list_final_call_info)), ensure_ascii=False)
    return json_data

def month_consume(data:dict):
    list_consume = []
    basic_fee = data['month_basic_fee']
    number = data['user_number']
    for each_month_call in data['call_info']:
        dict_month_consume = {}
        month = each_month_call['month']
        comsumed_fee = each_month_call['month_count']['month_fee']
        call_times = each_month_call['month_count']['call_total_num']
        call_durations = each_month_call['month_count']['call_total_time']
        list_calling_durations = []
        list_called_durations = []

        for each_call in each_month_call['call_info']:

            call_type = each_call['call_type']
            call_duration = each_call['call_duration']

            if call_type == '主叫':
                if call_duration ==' ':
                    call_duration = 0
                    list_calling_durations.append(call_duration)
                else:
                    list_calling_durations.append(call_duration)
            else:
                if call_duration == ' ':
                    call_duration = 0
                    list_called_durations.append(call_duration)
                else:
                    list_called_durations.append(call_duration)
        dict_month_consume['number'] = int(number)
        dict_month_consume['month'] = int(month)
        dict_month_consume['calling_times'] = len(list_calling_durations)
        dict_month_consume['calling_durations'] = sum(list_calling_durations)
        dict_month_consume['called_times'] = len(list_called_durations)
        dict_month_consume['called_durations'] = sum(list_called_durations)
        dict_month_consume['basic_fee'] = float(basic_fee)
        dict_month_consume['consumed_fee'] = float(comsumed_fee)
        dict_month_consume['call_times'] = call_times
        dict_month_consume['call_durations'] = sum(list_calling_durations) + sum(list_called_durations)
        list_consume.append(dict_month_consume)
    json_data = json.dumps(dict(zip(range(len(list_consume)), list_consume)), ensure_ascii=False)
    return json_data


'---------------------------------------------------------JD Extend----------------------------------------------------'

#订单基本信息
def get_orders_info(data):
    list_item_quantity = []
    list_item_amount = []
    order_num = len(data)
    dict_temp = {}
    for each_data in data:
        order_amount = 0 if not each_data['sum_price'] else float(each_data['sum_price'])
        list_item_amount.append(float(order_amount))
        item_quantity = 0 if not each_data['item_quantity'] else each_data['item_quantity']
        list_item_quantity.append(float(item_quantity))
    total_orders = order_num
    order_amount = sum(list_item_amount)
    single_highest = max(list_item_amount)
    ave_amonut = average(list_item_amount)
    item_quantities = sum(list_item_quantity)
    dict_temp['total_orders'] = total_orders
    dict_temp['order_amount'] = order_amount
    dict_temp['single_highest'] = single_highest
    dict_temp['ave_amonut'] = ave_amonut
    dict_temp['item_quantities'] = item_quantities
    return dict_temp
#消费信息

def get_month_consume(data):
    dict_month_comsume = {'01':{'count':[], 'amount':[]},
                          '02': {'count': [], 'amount': []},
                          '03': {'count': [], 'amount': []},
                          '04': {'count': [], 'amount': []},
                          '05': {'count': [], 'amount': []},
                          '06': {'count': [], 'amount': []},
                          '07': {'count': [], 'amount': []},
                          '08': {'count': [], 'amount': []},
                          '09': {'count': [], 'amount': []},
                          '10': {'count': [], 'amount': []},
                          '11': {'count': [], 'amount': []},
                          '12': {'count': [], 'amount': []}}

    for each_data in data:
        order_date = each_data['deal_time']
        month = get_month(order_date)
        item_quantity = 0 if not each_data['item_quantity'] else int(each_data['item_quantity'])
        item_amount = 0 if not  each_data['sum_price'] else float(each_data['sum_price'])
        dict_month_comsume[str(month)]['count'].append(item_quantity)
        dict_month_comsume[str(month)]['amount'].append(item_amount)
        dict_month_comsume[str(month)]['count'] = [sum(dict_month_comsume[str(month)]['count'])]
        dict_month_comsume[str(month)]['amount'] = [sum(dict_month_comsume[str(month)]['amount'])]
    for each in dict_month_comsume:
        dict_month_comsume[each]['count'] = 0 if not dict_month_comsume[each]['count'] else dict_month_comsume[each]['count'][0]
        dict_month_comsume[each]['amount'] = 0 if not dict_month_comsume[each]['amount'] else dict_month_comsume[each]['amount'][0]
    json_data = json.dumps(dict_month_comsume, ensure_ascii=False)
    return json_data


#收货地址信息
def get_address_order(data):
    list_consignees = []
    for i in data['order_info']:
        name = i['consignee']
        address= i['consignee_address']
        dict_address_order = {'name': name, 'address': address, 'phone':[], 'count':[], 'amount':[]}
        list_consignees.append(dict_address_order)

    for each in list_consignees:
        for each_data in data['order_info']:
            address = each_data['consignee_address']
            phone = each_data['consignee_phone']
            name = each_data['consignee']
            count = 0 if not each_data['item_quantity'] else int(each_data['item_quantity'])
            amount = 0 if not  each_data['sum_price'] else float(each_data['sum_price'])
            if name == each['name'] and address == each['address']:
                each['phone'].append(phone)
                each['count'].append(count)
                each['amount'].append(amount)
                each['count'] = [sum(each['count'])]
                each['amount'] = [sum(each['amount'])]
    from collections import OrderedDict
    temp = OrderedDict()
    for item in list_consignees:
        temp.setdefault(item['address'], {**item})

    for each in temp:
        temp[each]['phone'] = list(set(temp[each]['phone']))
        temp[each]['count'] =temp[each]['count'][0]
        temp[each]['amount'] = temp[each]['amount'][0]
    json_data = json.dumps(temp, ensure_ascii=False)
    return json_data