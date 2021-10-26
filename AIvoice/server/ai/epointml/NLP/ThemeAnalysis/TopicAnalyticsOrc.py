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

import pandas as pd
import os
from util.DBUtil import DbPoolUtil

from computeTopicWords import bient_kw

from config.settings import *

from TopicWorker import WorkPre, NewWorkorder

from pyltp import Segmentor, Postagger

from epNer import Ner

import codecs

import uuid

import copy

import time

if not os.path.exists("gen"):
    os.mkdir("gen")
if not os.path.exists("gen/img"):
    os.mkdir("gen/img")


def get_data():
    os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'

    con = DbPoolUtil(db_type='oracle')

    sql = """SELECT CASE_SERIAL, CASE_TITLE, CASE_CONTENT, date_format(CASE_DATE,'%%Y-%%m-%%d %%H:%%i:%%S'),CASE_TYPE FROM CASE_INFO where case_date <='2010-01-01 00:00:00'"""

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

    print("save key words to gen/kw.csv !")

    with codecs.open("gen/kw.csv", "w", encoding='utf-8') as f:

        for w in ret:

            if (wt[w] in ['n', 'ns', 'vn', 'nr']) and (len(w) > 1):
                line = str(w) + ', ' + str(ret[w]) + ',' + str(wt[w]) + '\n'

                f.write(line)


def mainTopicAnalytics():
    cws_model_path = os.path.join(LTPMODEL_PATH, 'cws.model')  # 分词模型路径，模型名称为`cws.model`

    pos_model_path = os.path.join(LTPMODEL_PATH, 'pos.model')  # 词性标模型注模型，模型名称为'pos.model'
    segmentor = Segmentor()  # 初始化分词器实例
    segmentor.load_with_lexicon(cws_model_path, os.path.join(INPUTFILE_PATH, 'lexicon.txt'))  # 加载模型
    postagger = Postagger()  # 初始化词性标注实例
    postagger.load_with_lexicon(pos_model_path, os.path.join(INPUTFILE_PATH, 'wordtag.txt'))  # 加载模型
    wi = NewWorkorder()
    wi.initial()
    wp = WorkPre()
    wner = Ner()
    # ft, st, address = wi.getWorkorders(workordersPre=wp, segmentor=segmentor, postagger=postagger, ner=wner, content=sen)
    con = DbPoolUtil(db_type='mysql')
    sql = "SELECT CASE_SERIAL, CASE_TITLE, CASE_CONTENT, AREA_CODE, CASE_DATE, CASE_SOURCE,CASE_TYPE FROM CASE_INFO where case_date <='2010-01-01 00:00:00'"

    con = DbPoolUtil(db_type='mysql')
    sql = """SELECT CASE_SERIAL, CASE_TITLE, CASE_CONTENT, AREA_CODE, OPERATEDATE, CASE_SOURCE FROM CASE_INFO"""
    sl  = con.execute_query(sql)

    con = DbPoolUtil(db_type='mysql')
    sql = """SELECT CASE_SERIAL, CASE_TITLE, CASE_CONTENT, AREA_CODE, OPERATEDATE, CASE_SOURCE FROM CASE_INFO LIMIT 50000"""
    sl  = con.execute_query(sql)

    sl = con.execute_query(sql)

    ret = []
    for case in sl:
        try:
            sen = "{0};{1}".format(str(case[1]), str(case[2]))
            ft, st, address = wi.getWorkorders(workordersPre=wp, segmentor=segmentor, postagger=postagger, ner=wner,
                                               content=sen)
            stl = st.split(';')
            k = len(stl)
            if k > 4:
                for i in range(4):
                    tstl = copy.deepcopy(stl)
                    tstl.remove(stl[i])
                    line = [str(uuid.uuid1()), str(ft), str(st), str(case[0]), str(address), str(case[3]),
                            case[4].strftime('%Y-%m-%d %H:%I:%S'), str(case[5]), str(stl[i]), ";".join(tstl),
                            str(case[1]), str(case[2]), str(case[6])]
                    ret.append(line)
            elif k > 1:
                for i in range(k):
                    tstl = copy.deepcopy(stl)
                    tstl.remove(stl[i])
                    line = [str(uuid.uuid1()), str(ft), str(st), str(case[0]), str(address), str(case[3]),
                            case[4].strftime('%Y-%m-%d %H:%I:%S'), str(case[5]), str(stl[i]), ";".join(tstl),
                            str(case[1]), str(case[2]), str(case[6])]
                    ret.append(line)
            else:
                line = [str(uuid.uuid1()), str(ft), str(st), str(case[0]), str(address), str(case[3]),
                        case[4].strftime('%Y-%m-%d %H:%I:%S'), str(case[5]), str(st), None, str(case[1]), str(case[2]),
                        str(case[6])]
                ret.append(line)
        except:
            segmentor = Segmentor()  # 初始化分词器实例
            segmentor.load_with_lexicon(cws_model_path, os.path.join(INPUTFILE_PATH, 'lexicon.txt'))  # 加载模型
            postagger = Postagger()  # 初始化词性标注实例
            postagger.load_with_lexicon(pos_model_path, os.path.join(INPUTFILE_PATH, 'wordtag.txt'))  # 加载模型
            continue

    # 写回数据： ROWGUID, FIRST_TOPIC, SEC_TOPIC, CASE_SERIAL, CASE_LOCATION, AREA_CODE, CASE_DATE, APPLICANT_SOURCE, L2, L3

    # 结果写回数据库

    os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'

    sql2 = "INSERT INTO TOPIC_ANALYTICS(ROWGUID, FIRST_TOPIC, SEC_TOPIC, CASE_SERIAL, CASE_LOCATION, AREA_CODE, CASE_DATE, CASE_SOURCE, L2, L3, CASE_TITLE, CASE_CONTENT,CASE_TYPE) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    print("Start inserting result to MySQL. ")
    con.execute_many_iud(sql2, ret)
    segmentor.release()
    postagger.release()


if __name__ == "__main__":
    # 获取数据
    # df = get_data()
    # 提取关键词
    # kw(df)
    mainTopicAnalytics()