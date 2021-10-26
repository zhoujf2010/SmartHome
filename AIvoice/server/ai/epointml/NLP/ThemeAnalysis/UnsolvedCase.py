# -*- coding: utf-8 -*-
"""
久拖不决问题识别
"""
from util.DBUtil import DbPoolUtil
import os
import pandas as pd
import datetime


class UnsolvedCase:
    def __init__(self):
        pass

    def create_table(self):
        os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'
        sql = """DELETE FROM EVENT_ANALYTICS"""
        con = DbPoolUtil(db_type='oracle')
        con.execute_iud(sql)

    def unvolced_analysis(self):
        os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'
        sql = """SELECT ROWGUID, EVENT_NAME, EVENT_TIME, EVENT_LOCATION, ANALYSIS_NAME, EVENT_JSON FROM EVENT_ANALYTICS"""
        con = DbPoolUtil(db_type='oracle')
        ret = con.execute_query(sql)
        df = pd.DataFrame(ret, columns=['ROWGUID', 'EVENT_NAME', 'EVENT_TIME', 'EVENT_LOCATION', 'ANALYSIS_NAME', 'EVENT_JSON'])
        k = len(df)
        df['START_TIME'] = [None] * k
        df['LAST_TIME'] = [None] * k
        df['EVENT_PERIOD'] = [None] * k
        df['SATISFY'] = [None] * k
        for i in range(k):
            event_json = eval(str(df['EVENT_JSON'][i]))
            if event_json is None:
                pass
            elif len(event_json) == 1:
                df.loc[i, 'START_TIME'] = datetime.datetime.strptime(event_json[0][0],'%Y-%m-%d')
                df.loc[i, 'EVENT_PERIOD'] = 1
            elif len(event_json) > 1:
                df.loc[i, 'START_TIME'] = datetime.datetime.strptime(event_json[0][0], '%Y-%m-%d')
                df.loc[i, 'LAST_TIME'] = datetime.datetime.strptime(event_json[-1][0],'%Y-%m-%d')
                st = event_json[0][0].split('-')
                lt = event_json[-1][0].split('-')
                df.loc[i, 'EVENT_PERIOD'] = (int(lt[0]) - int(st[0]))*365 + (int(lt[1])-int(st[1]))*30 + (int(lt[2])-int(st[2])+1)
            sql = """SELECT EC.VISIT_SATIFY FROM 
                    EVENT_ANALYSIS_TEMP EA, CASE_VISIT_INFO EC
                    WHERE EA.EVENT_SERIAL='{0}' AND EA.CASE_SERIAL = EC.CASE_SERIAL""".format(str(df['ROWGUID'][i]))
            rs = con.execute_query(sql)
            if len(rs) > 0:
                rl = [i[0] for i in rs]
                vs = rl.count('3')
                bs = rl.count('2')
                us = rl.count('1')
                df.loc[i, 'SATISFY'] = "{0};{1};{2}".format(us,bs,vs)
        data = df.values.tolist()
        # for r in data:
        #     print(r)
        sql = """INSERT INTO UNSOLVED_EVENT_INFO(ROWGUID, EVENT_NAME, EVENT_TIME, EVENT_LOCATION, ANALYSIS_NAME, EVENT_JSON,
        START_TIME, LAST_TIME, EVENT_PERIOD, SATISFY) VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10)"""
        con.execute_many_iud(sql, data)


if __name__ == '__main__':
    uc = UnsolvedCase()
    uc.unvolced_analysis()