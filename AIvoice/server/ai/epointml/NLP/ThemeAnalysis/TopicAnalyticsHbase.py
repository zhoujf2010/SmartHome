# -*- coding: utf-8 -*-
"""
12345工单分析通用流程框架
    实现功能：
            1. 从oracle数据库获取数据
            2. 通过信息熵计算关键词
            3. 共现词聚类

@auther: Adrian
@date: 2018/7/10
"""
import cx_Oracle
import pandas as pd
import os
from algorithms import hoc
import jieba
import matplotlib.pyplot as plt
import matplotlib.dates as mdate
from algorithms.KeywordExtraction.chinese_stop_words import  chinese_stop_words
from util.DBUtil import DbPoolUtil
from algorithms.KeywordExtraction.entropy_keywords import bient_kw
import codecs


# 写入词典文件
if not os.path.exists("config/dict.txt"):
    con = DbPoolUtil(db_type='mysql')
    sql = """select word, freq, type from dict_default"""
    data_default = con.execute_query(sql)
    sql = """select word, freq, type from dict_nj12345"""
    data_nj = con.execute_query(sql)

    with codecs.open("config/dict.txt", "w", encoding="utf-8") as f:
        for i in data_default:
            if i[2] is None:
                line = "{0} {1} \n".format(str(i[0]), i[1])
            else:
                line = "{0} {1} {2} \n".format(str(i[0]), i[1], i[2])
            f.write(line)
        for i in data_nj:
            line = "{0} {1} {2} \n".format(str(i[0]), "200", "n")
            f.write(line)

jieba.set_dictionary("config/dict.txt")

if not os.path.exists("gen/"):
    os.mkdir("gen/")

if not os.path.exists("gen/img"):
    os.mkdir("gen/img")


def get_data():
    con = DbPoolUtil(db_type='hbase')
    sql = """
        SELECT  CASE_SERIAL, CASE_TITLE, CASE_CONTENT, CASE_DATE
        FROM 
        CASE_INFO LIMIT 100
    """
    ret = con.execute_query(sql)
    # print(ret)

    df = pd.DataFrame(ret, columns=["case_serial", "case_title", "case_content", "case_date"])
    print("Save case data to gen/casedata.xlsx")
    df.to_excel("gen/casedata.xlsx", index=None)
    return df


def kw(df=None):
    """
    关键词提取
    :param df: 工单 data frame
    :return:
    """
    if df is None:
        df = pd.read_excel("gen/casedata.xlsx")
    data = ""
    for i in range(len(df)):
        data += str(df['case_title'][i]) + ',' + str(df['case_content'][i])
    ret, wt = bient_kw(src=data, minC=50)

    print("save key word to gen/kw.csv !")
    with codecs.open("gen/kw.csv", "w", encoding='utf-8') as f:
        for w in ret:
            if (wt[w] in ['n' ,'ns', 'vn', 'nr']) and (len(w) > 1):
                line = str(w) + ', ' + str(ret[w]) + ',' + str(wt[w]) + '\n'
                f.write(line)


def cluster():
    """
    共现词聚类
    :return:
    """
    dfw = pd.read_csv("gen/kw.csv", header=None, encoding='utf-8')
    dfw = list(dfw[0])

    df_stop = pd.read_excel("gen/stop.xlsx")
    stop = set(list(df_stop['Word']))
    dfw = list(set(dfw) - set(chinese_stop_words) - stop)

    # 读取需要用于聚类的case数据
    df_case = pd.read_excel("gen/education.xlsx")
    # hoc.con_clustering(dfw, df_case, dst="gen/result_1000.xlsx")

    # 单层聚类，将聚类结果写入 gen/result_1000.xlsx
    # hoc.con_clustering_one_level(dfw, df_case, dst="gen/result_1000.xlsx")
    rst = hoc.con_clustering(dfw, df_case, dst="gen/result_nj.xlsx")

    # 结果写回数据库
    con = DbPoolUtil(db_type='hbase')


    sql1 = """DELETE FROM TOPIC_ANALYTICS"""
    con.execute_iud(sql1)

    sql2 = """
        UPSERT INTO TOPIC_ANALYTICS(CASE_SERIAL, CASE_TITLE, CASE_CONTENT, FIRST_TOPIC, SEC_TOPIC)
        VALUES (?, ?, ?, ?, ?)
    """
    print("start inserting result to hbase. ")
    con.execute_many_iud(sql2, rst)


def growth_activity(sql=None):
    """
    Analysis - 批量提取少量但是增长事件
    :param sql:
    :return:
    """
    connection = DbPoolUtil(db_type='oracle')
    if sql is None:
        x = connection.execute_query("""
            SELECT 
                CB.CASE_TITLE, CB.CASE_CONTENT, CB.CASE_SERIAL, CB.TOPIC, CA.CASE_DATE
            FROM 
                CASE_INFO CA, CASE_TOPIC CB
            WHERE CA.CASE_SERIAL = CB.CASE_SERIAL
            """)
    else:
        x = connection.execute_query(sql)
    df_case = pd.DataFrame(x, columns=['CASE_TITLE', 'CASE_CONTENT', 'CASE_SERIAL', 'TOPIC', 'CASE_DATE'])
    # df_case['CASE_DATE'] = pd.to_datetime(df_case['CASE_DATE'], unit='D')
    df_case['CASE_DATE'] = df_case['CASE_DATE'].dt.date

    del x

    # distinct topic
    topic = set(list(df_case['TOPIC']))

    for word in topic:
        df = df_case[df_case['TOPIC']== word]
        tdf = df.groupby('CASE_DATE').CASE_SERIAL.nunique()

        fig1 = plt.figure(figsize=(15, 10))
        ax1 = fig1.add_subplot(1, 1, 1)
        ax1.xaxis.set_major_formatter(mdate.DateFormatter('%Y-%m-%d'))  # 设置时间标签显示格式
        plt.xticks(list(tdf.index), rotation=90)
        plt.plot(list(tdf.index), list(tdf), 'o-')
        plt.savefig('gen/img/{0}.png'.format(str(word)))


if __name__ == "__main__":
    # 获取数据
    df = get_data()
    # 提取关键词
    kw(df)
    # 共现层次聚类
    cluster()

    # insert_test()
    # 事件趋势分析
    # sql = """
    #     SELECT CASE_TITLE, CASE_CONTENT, CASE_SERIAL, FIRST_TOPIC, CASE_DATE
    #     FROM TOPIC_ANALYTICS WHERE
    #         CASE_CONTENT LIKE '%水体%' OR CASE_CONTENT LIKE '%堆场%' OR CASE_CONTENT LIKE '%环境很差%' OR CASE_CONTENT LIKE '%发绿%' OR CASE_CONTENT LIKE '%黑水%' OR CASE_CONTENT LIKE '%宁静%' OR CASE_CONTENT LIKE '%每况愈下%' OR CASE_CONTENT LIKE '%破坏生态环境%' OR CASE_CONTENT LIKE '%发浑%' OR CASE_CONTENT LIKE '%脏乱差%' OR CASE_CONTENT LIKE '%环境卫生很差%' OR CASE_CONTENT LIKE '%气味%' OR CASE_CONTENT LIKE '%很糟糕%' OR CASE_CONTENT LIKE '%周边环境%' OR CASE_CONTENT LIKE '%定期打扫%' OR CASE_CONTENT LIKE '%排放工业%' OR CASE_CONTENT LIKE '%偷排行%' OR CASE_CONTENT LIKE '%污染气体%' OR CASE_CONTENT LIKE '%油气%' OR CASE_CONTENT LIKE '%塑料产品%' OR CASE_CONTENT LIKE '%空气污染%' OR CASE_CONTENT LIKE '%卫生环境%' OR CASE_CONTENT LIKE '%整体环境%' OR CASE_CONTENT LIKE '%脏乱%' OR CASE_CONTENT LIKE '%及时清理%' OR CASE_CONTENT LIKE '%排放%' OR CASE_CONTENT LIKE '%偷排%' OR CASE_CONTENT LIKE '%防治措施%' OR CASE_CONTENT LIKE '%环境污染%' OR CASE_CONTENT LIKE '%污染%' OR CASE_CONTENT LIKE '%造成空气污染%' OR CASE_CONTENT LIKE '%黑沙%' OR CASE_CONTENT LIKE '%土壤%' OR CASE_CONTENT LIKE '%污染严重%' OR CASE_CONTENT LIKE '%废水%' OR CASE_CONTENT LIKE '%毒气%' OR CASE_CONTENT LIKE '%噪声%' OR CASE_CONTENT LIKE '%废旧家具%' OR CASE_CONTENT LIKE '%整治%' OR CASE_CONTENT LIKE '%木材厂%' OR CASE_CONTENT LIKE '%饱受%' OR CASE_CONTENT LIKE '%固废%' OR CASE_CONTENT LIKE '%工厂%' OR CASE_CONTENT LIKE '%卫生%' OR CASE_CONTENT LIKE '%苍蝇蚊虫%' OR CASE_CONTENT LIKE '%环境脏乱差%' OR CASE_CONTENT LIKE '%河中%' OR CASE_CONTENT LIKE '%切切实实%' OR CASE_CONTENT LIKE '%空气%' OR CASE_CONTENT LIKE '%招蚊虫%' OR CASE_CONTENT LIKE '%反而越来越%' OR CASE_CONTENT LIKE '%填埋场%' OR CASE_CONTENT LIKE '%溢满%' OR CASE_CONTENT LIKE '%粉尘%' OR CASE_CONTENT LIKE '%污染环境%' OR CASE_CONTENT LIKE '%饵料%' OR CASE_CONTENT LIKE '%坏境%' OR CASE_CONTENT LIKE '%烟尘%' OR CASE_CONTENT LIKE '%河源%' OR CASE_CONTENT LIKE '%环境卫生%' OR CASE_CONTENT LIKE '%生产作业%' OR CASE_CONTENT LIKE '%变黑%' OR CASE_CONTENT LIKE '%整洁%' OR CASE_CONTENT LIKE '%木屑%' OR CASE_CONTENT LIKE '%鸡粪%' OR CASE_CONTENT LIKE '%鼠蚁%' OR CASE_CONTENT LIKE '%黑烟%'
    #     order by FIRST_TOPIC
    # """
    # growth_activity(sql)

