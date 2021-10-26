# -*- coding: utf-8 -*-
from util.DBUtil import DbPoolUtil
import pandas as pd
import os
import copy


def nut():
    os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'
    con = DbPoolUtil(db_type='oracle')
    sql = """SELECT CASE_SERIAL, SEC_TOPIC FROM TOPIC_ANALYTICS WHERE L2 IS NULL """
    ret = con.execute_query(sql)
    df = pd.DataFrame(ret, columns=['id', 'topic'])
    for i in range(len(df)):
        try:
            topic = str(df['topic'][i]).strip().split(";")
            if len(topic) == 0:
                continue
            elif len(topic) == 1:
                sql = """UPDATE TOPIC_ANALYTICS SET L2='{0}' WHERE CASE_SERIAL = '{1}'""".format(topic[0], df['id'][i])
                con.execute_iud(sql)
            elif len(topic) == 2:
                sql = """UPDATE TOPIC_ANALYTICS SET L2='{0}', L3='{1}' 
                WHERE CASE_SERIAL = '{2}'""".format(topic[0],topic[1], df['id'][i])
                con.execute_iud(sql)
            elif len(topic) == 3:
                sql = """UPDATE TOPIC_ANALYTICS SET L2='{0}', L3='{1}', l4='{2}'
                WHERE CASE_SERIAL = '{3}'""".format(topic[0], topic[1], topic[2], df['id'][i])
                con.execute_iud(sql)
            elif len(topic) >3:
                sql = """UPDATE TOPIC_ANALYTICS SET L2='{0}', L3='{1}', L4='{2}', L5='{3}'
                WHERE CASE_SERIAL = '{4}'""".format(topic[0], topic[1], topic[2], topic[3], df['id'][i])
                con.execute_iud(sql)
        except Exception as err:
            print(err)


def nut2():
    """
    TOPIC_ANALYTICS生成程序， 从topic_analytics表中读数据，改成树形结构写入。
    :return:
    """
    os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'
    con = DbPoolUtil(db_type='oracle')
    sql = """SELECT FIRST_TOPIC, SEC_TOPIC, CASE_SERIAL, AREA_CODE, CASE_DATE
            FROM TOPIC_ANALYTICS """
    ret = con.execute_query(sql)
    df = pd.DataFrame(ret, columns=['first_topic', 'sec_topic', 'case_serial', 'area_code', 'case_date'])
    inst = [] # 插入结果表
    for i in range(len(df)):
        try:
            topic = str(df['sec_topic'][i]).strip().split(";")
            k = len(topic)
            if k == 1:
                if topic[0] == 'None':
                    inst.append([df['first_topic'][i], df['sec_topic'][i], df['case_serial'][i], df['area_code'][i],
                                 df['case_date'][i], None, None])
                else:
                    inst.append([df['first_topic'][i], df['sec_topic'][i], df['case_serial'][i], df['area_code'][i],
                                 df['case_date'][i], topic[0], None])
            elif k == 2:
                inst.append([df['first_topic'][i], df['sec_topic'][i], df['case_serial'][i], df['area_code'][i],
                             df['case_date'][i], topic[0], topic[1]])
                inst.append([df['first_topic'][i], df['sec_topic'][i], df['case_serial'][i], df['area_code'][i],
                             df['case_date'][i], topic[1], topic[0]])
            elif k == 3:
                for v in topic:
                    topic_tmp = copy.deepcopy(topic)
                    topic_tmp.remove(v)
                    inst.append([df['first_topic'][i], df['sec_topic'][i], df['case_serial'][i], df['area_code'][i],
                             df['case_date'][i], v, ";".join(topic_tmp)])
            elif k > 3:
                for v in topic[:4]:
                    topic_tmp = copy.deepcopy(topic)
                    topic_tmp.remove(v)
                    inst.append([df['first_topic'][i], df['sec_topic'][i], df['case_serial'][i], df['area_code'][i],
                             df['case_date'][i], v, ";".join(topic_tmp)])
        except Exception as err:
            print(err)

    print("写入工单数据量：")
    print(len(inst))
    sql = """INSERT INTO TOPIC_ANALYTICS_TEMP(FIRST_TOPIC, SEC_TOPIC, CASE_SERIAL, AREA_CODE, CASE_DATE, L2, L3)
        VALUES (:1, :2, :3, :4, :5, :6, :7)"""
    con.execute_many_iud(sql, inst)


if __name__ == "__main__":
    nut2()

