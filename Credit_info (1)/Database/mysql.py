from Config.config import mysql_connect
conn = mysql_connect()
cursor = conn.cursor()
#运营商表和插入
def create_operator():
    sql = """
        create table tb_operator_info(
            id int(5) NOT NULL auto_increment COMMENT 'id',
            source int(5) NOT NULL COMMENT '来源',
            regis_id bigint(50) NOT NULL COMMENT  '注册身份证号',
            regis_name varchar(64) NOT NULL COMMENT '注册姓名',
            regis_address varchar(128) NOT NULL COMMENT '注册地址',
            regis_date varchar(64) NOT NULL COMMENT '注册日期',
            inter_call_num  int(30) NOT NULL COMMENT '户通过电话的号码数量',
            num_time int(30) NOT NULL COMMENT '号码使用时间',
            night_call int(30) NOT NULL COMMENT '夜间通话数量',
            silent int(30) NOT NULL COMMENT '手机静默天数',
            longest_silent int(30) NOT NULL COMMENT '最长手机静默天数',
            recent_silent int(30) NOT NULL COMMENT '最近静默天数',
            ave_fee decimal(10,2) NOT NULL COMMENT '月平均消费',
            last_fee decimal(10,2) NOT NULL COMMENT '上个月消费',
            spe_call int(10) NOT NULL COMMENT '特殊电话',
            comsume text NOT NULL COMMENT '手机消费信息',
            area text NOT NULL COMMENT '手机消费信息',
            top_5_duration text NOT NULL COMMENT 'Top5高频联系人',
            top_5_times text NOT NULL COMMENT 'Top5长时间联系人',
            call_info text NOT NULL COMMENT '手机通话信息',
            PRIMARY KEY (id)
            )
    """
    cursor.execute(sql)
    conn.commit()
    conn.close()
    return conn

def insert_opertor_sql(value):
    conn = mysql_connect()
    cursor = conn.cursor()
    sql_insert = """
        INSERT INTO tb_operator_info
        (source, regis_id, regis_name, regis_address, regis_date, inter_call_num, num_time, night_call, silent,
        longest_silent, recent_silent, ave_fee, last_fee, spe_call, consume, area, top_5_duration, top_5_times,
        call_info)
        VALUES {}  
    """.format(value)
    cursor.execute(sql_insert)
    conn.commit()
    conn.close()
    return conn



#电商平台表和插入
def create_buy_info():
    sql = """
        create table tb_buy_info(
            id int(5) NOT NULL auto_increment COMMENT 'id',
            source int(5) NOT NULL COMMENT '来源',
            name varchar(64) DEFAULT NULL COMMENT '姓名',
            regis_num bigint(50) NOT NULL COMMENT  '注册身份证号',
            bai_tiao varchar(64) NOT NULL COMMENT '白条开通状态',
            balanced varchar(128) NOT NULL COMMENT '剩余额度/总额度',
            bai_score varchar(64) NOT NULL COMMENT '小白信用',
            card_info  text NOT NULL COMMENT '银行卡信息',
            address_info text NOT NULL COMMENT '收货地址信息',
            total_orders int(30) NOT NULL COMMENT '订单数',
            order_amount int(30) NOT NULL COMMENT '订单总金额',
            single_highest int(30) NOT NULL COMMENT '单笔最高金额',
            ave_amonut float(30) NOT NULL COMMENT '订单平均金额',
            item_quantities int(30) NOT NULL COMMENT '商品数量',
            month_order text  NOT NULL COMMENT '消费信息(按月)',
            address_order text NOT NULL COMMENT '收货地址计算收货量',
            PRIMARY KEY (id)
            )
    """
    cursor.execute(sql)
    conn.commit()
    conn.close()
    return conn

def insert_buy_sql(value):
    conn = mysql_connect()
    cursor = conn.cursor()
    sql_insert = """
        INSERT INTO tb_buy_info
         (source, name, regis_num, bai_tiao, balanced, bai_score, card_info,
         address_info, total_orders, order_amount, single_highest, ave_amonut,
         item_quantities, month_order, address_order)
        VALUES {}  
    """.format(value)
    cursor.execute(sql_insert)
    conn.commit()
    conn.close()
    return conn





#QQ通讯录建表
def create_QQIC_info():
    sql = """
        create table tb_QQIC_info(
            id int(5) NOT NULL auto_increment COMMENT 'id',
            source int(5) NOT NULL COMMENT '来源',
            name varchar(64) DEFAULT NULL COMMENT '用户',
            contact text NOT NULL COMMENT '联系人信息',
            captcha_path varchar(120) NOT NULL COMMENT '验证码地址',
            PRIMARY KEY (id)
            )
    """
    cursor.execute(sql)
    conn.commit()
    conn.close()
    return conn
#QQ通讯录插入mysql
def insert_QQIC_sql(value):
    conn = mysql_connect()
    cursor = conn.cursor()
    sql_insert = """
        INSERT INTO tb_QQIC_info
         (source, name, contact, captcha_path)
        VALUES {}  
    """.format(value)
    cursor.execute(sql_insert)
    conn.commit()
    conn.close()


#今借到mysql建表
def create_JJD_info():
    sql = """
        create table tb_JJD_info(
            id int(5) NOT NULL AUTO_INCREMENT COMMENT 'id',
            balance FLOAT(30) NOT NULL COMMENT '余额',
            source INT(5) NOT NULL COMMENT '来源',
            name VARCHAR(64) NOT NULL COMMENT '用户',
            number BIGINT(50) NOT NULL  COMMENT '手机号',
            need_2_pay FLOAT(30) NOT NULL COMMENT '待还金额',
            total_amount FLOAT(30) NOT NULL COMMENT '当前借入金额',
            max_amount FLOAT(30) NOT NULL COMMENT '最大借入金额',
            count INT(64) NOT NULL COMMENT '累计借入笔数',
            count_people INT(64) NOT NULL COMMENT '累计借入人数',
            instant_pay_rate FLOAT(30) NOT NULL COMMENT '当日进入当日还款比率',
            borrow text NOT NULL COMMENT '联系人信息',
            max_need_2_pay FLOAT(30) NOT NULL COMMENT '最大待还金额',
            interest_2_pay FLOAT(30) NOT NULL COMMENT '应付利息',
            borrow_times INT(30) NOT NULL COMMENT '借入次数',
            PRIMARY KEY (id)
            )
    """
    cursor.execute(sql)
    conn.commit()
    conn.close()
    return conn

#今借到mysql插入
def insert_JJD_sql(value):
    conn = mysql_connect()
    cursor = conn.cursor()
    sql_insert = """
        INSERT INTO tb_JJD_info
         (source, name, number, balance, need_2_pay, total_amount,max_amount,count,count_people,instant_pay_rate,borrow,max_need_2_pay,interest_2_pay,borrow_times)
        VALUES {}  
    """.format(value)
    cursor.execute(sql_insert)
    conn.commit()
    conn.close()


