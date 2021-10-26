# -*- coding: utf-8 -*-
from util.DBUtil import DbPoolUtil
import pandas as pd
import os
import json
import datetime


class EventMot():
    def __init__(self):
        pass

    def delete_analytics(self):
        os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'
        sql = """DELETE FROM EVENT_ANALYTICS"""
        con = DbPoolUtil(db_type='mysql')
        con.execute_iud(sql)

    def insert_all(self):
        """
        全量从temp表中写入事件
        :return:
        """
        os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'
        sql = """SELECT date_format(CASE_DATE,{}), CASE_LOCATION, ANALYSIS_NAME, EVENT_SERIAL  from EVENT_ANALYSIS_TEMP""".format('"%%Y-%%m-%%d"')
        con = DbPoolUtil(db_type='mysql')
        ret = con.execute_query(sql)
        df = pd.DataFrame(list(ret), columns=['date', 'location', 'name', 'serial'])
        df_name = list(df['serial'].drop_duplicates())

        # 结果存储[event_serial, analysis_name, case_date, case_location, json]
        rst = []
        for i in df_name:
            dft = df[df['serial']==i].copy()
            ml = dft.location.str.len().max() # max location index
            rtmp = [str(dft.iloc[0]['serial']), str(dft.iloc[0]['name']), datetime.datetime.strptime(str(dft.iloc[0]['date']), '%Y-%m-%d'),
                    str(df['location'][ml]), self.timeseris_json(dft, i)]
            rst.append(rtmp)
        sql = """INSERT INTO EVENT_ANALYTICS(ROWGUID, ANALYSIS_NAME, EVENT_TIME, EVENT_LOCATION, EVENT_JSON) VALUES
        (%s,%s,%s,%s,%s)"""
        con.execute_many_iud(sql, rst)

    # 增量写入
    def incremental_insert(self):
        # os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'
        sql = """SELECT CASE_DATE, CASE_LOCATION, ANALYSIS_NAME, EVENT_SERIAL  from EVENT_ANALYSIS_TEMP
        WHERE EVENT_SERIAL NOT IN (SELECT ROWGUID FROM EVENT_ANALYTICS) AND ROWNUM < 5"""
        con = DbPoolUtil(db_type='mysql')
        # print(sql)
        ret = list(con.execute_query(sql))
        # print(ret)
        if len(ret) > 0:
            df = pd.DataFrame(ret, columns=['date', 'location', 'name', 'serial'])
            df_name = list(df['serial'].drop_duplicates())
            # 结果存储[event_serial, analysis_name, case_date, case_location, json]
            rst = []
            for i in df_name:

                dft = df[df['serial'] == i].copy()

                ml = dft.location.str.len().idxmax()  # max location index

                ml = dft.location.str.len().max()  # max location index

                # print(i)
                ml = dft.location.str.len().idxmax()  # max location index

                rtmp = [str(dft.iloc[0]['serial']), str(dft.iloc[0]['name']),
                        datetime.datetime.strptime(str(dft.iloc[0]['date']), '%Y-%m-%d'),
                        str(df['location'][ml]), self.timeseris_json(dft, i),len(dft)]
                # print(self.timeseris_json(dft, i))

                rst.append(rtmp)
            sql = """INSERT INTO EVENT_ANALYTICS(ROWGUID, ANALYSIS_NAME, EVENT_TIME, EVENT_LOCATION, EVENT_JSON,
            eventcount)VALUES(%s,%s,%s,%s,%s,%s)"""
            print(sql)
            con.execute_many_iud(sql, rst)
        else:
            print("EVENT_ANALYTICS table is already updated.")

    def timeseris_json(self, df, name):
        # dft = df[df['serial']==name].copy()
        dftl = df.groupby(['date']).size().reset_index(name='size')
        dftl = dftl.dropna()
        j = []
        for i in range(len(dftl)):
            j.append([str(dftl['date'][i]), str(dftl['size'][i])])
        return json.dumps(j)


if __name__ == "__main__":
    em = EventMot()
    # em.delete_analytics()
    # em.insert_all()
    em.incremental_insert()