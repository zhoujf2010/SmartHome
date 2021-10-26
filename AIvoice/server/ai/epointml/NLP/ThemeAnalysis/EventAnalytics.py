# -*- coding: utf-8 -*-
from sklearn.metrics import pairwise_distances
from sklearn.cluster import DBSCAN
from sklearn import preprocessing
import numpy as np
import gensim
from util.DBUtil import DbPoolUtil
import codecs
import uuid
from collections import defaultdict


# Calculate wmf
def jaccard_distance(t1, t2):
    topic_one = t1.split(';')
    topic_two = t2.split(';')
    k1 = len(topic_one)
    k2 = len(topic_two)
    k3 = len(set(topic_one + topic_two))
    # print(set(topic_one) & set(topic_two))
    # print(k1, k2, k3)
    s = float(k1 + k2 - k3)
    ret = s / k3
    print(pairwise_distances(X=topic_one, Y=topic_two, metric='jaccard'))
    return ret


class EventWorker():
    def __init__(self, model_path, dim=200):
        self.model = gensim.models.Word2Vec.load(model_path)
        self.dim = dim

    def Vectorize(self, content, location):
        cntLst = content.split(";")
        k = 0.
        wordArray = np.array([0.] * self.dim)
        for word in cntLst:
            try:
                vec = np.array(self.model.wv[word])
                # print(vec)
                wordArray += vec
                k += 1
            except Exception as err:
                # print(err)
                # print(word)
                continue
        if k != 0:
            topicRst = wordArray / k
        else:
            topicRst = wordArray

        locLst = location.split(";")
        k = 0.
        locArray = np.array([0.] * self.dim)
        for loc in locLst:
            try:
                vec = np.array(self.model.wv[loc])
                locArray += vec
                k += 1
            except Exception:
                continue
        if k != 0:
            locRst = locArray / k
        else:
            locRst = locArray
        ret = np.hstack((topicRst, locRst))
        # print(ret)
        return ret


    def main_dbscan(self):
        con = DbPoolUtil(db_type='mysql')

        SQL = """SELECT CASE_SERIAL, SEC_TOPIC, CASE_DATE, CASE_TITLE, CASE_CONTENT, FIRST_TOPIC, CASE_LOCATION FROM TOPIC_ANALYTICS GROUP BY CASE_SERIAL limit 100000"""
        data = con.execute_query(SQL)
        dl = []
        for line in data:
            dl.append(self.Vectorize(content=line[1], location=line[6]))
        train_data = np.array(dl)
        # print(train_data)
        cluster = DBSCAN(eps=0.1, min_samples=5, metric='cosine', n_jobs=-1).fit_predict(X=train_data)
        clsGuid = dict()
        rst = []
        for i in range(len(cluster)):
            id = cluster[i]
            if id != -1:
                if id not in clsGuid.keys():
                    clsGuid[id] = {}
                    clsGuid[id]['guid'] = str(uuid.uuid1())
                    clsGuid[id]['name'] = str(data[i][1])
                line = [clsGuid[id]['guid'], str(data[i][0]), str(data[i][2]), str(data[i][3]), str(data[i][4]),
                        str(data[i][5]),
                        str(data[i][1]), str(data[i][6]), clsGuid[id]['name'], clsGuid[id]['guid']]
                rst.append(line)
        SQL = """INSERT INTO EVENT_ANALYSIS_TEMP (ROWGUID, CASE_SERIAL, CASE_DATE, CASE_TITLE, CASE_CONTENT, FIRST_TOPIC,
            SEC_TOPIC, CASE_LOCATION, ANALYSIS_NAME, EVENT_SERIAL) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        con.execute_many_iud(SQL, rst)

        SQL = """SELECT CASE_SERIAL, SEC_TOPIC, CASE_DATE, CASE_TITLE, CASE_CONTENT, FIRST_TOPIC, CASE_LOCATION FROM TOPIC_ANALYTICS GROUP BY CASE_SERIAL limit 10000"""
        data = con.execute_query(SQL)
        dl = []
        for line in data:
            dl.append(self.Vectorize(content=line[1], location=line[6]))
        train_data = np.array(dl)
        # print(train_data)
        cluster = DBSCAN(eps=0.1, min_samples=2, metric='cosine', n_jobs=-1).fit_predict(X=train_data)
        clsGuid = dict()
        rst = []
        for i in range(len(cluster)):
            id = cluster[i]
            if id != -1:
                if id not in clsGuid.keys():
                    clsGuid[id] = {}
                    clsGuid[id]['guid'] = str(uuid.uuid1())
                    clsGuid[id]['name'] = str(data[i][1])
                line = [clsGuid[id]['guid'], str(data[i][0]), str(data[i][2]), str(data[i][3]), str(data[i][4]),
                        str(data[i][5]),
                        str(data[i][1]), str(data[i][6]), clsGuid[id]['name'], clsGuid[id]['guid']]
                rst.append(line)
        SQL = """INSERT INTO EVENT_ANALYSIS_TEMP (ROWGUID, CASE_SERIAL, CASE_DATE, CASE_TITLE, CASE_CONTENT, FIRST_TOPIC,
            SEC_TOPIC, CASE_LOCATION, ANALYSIS_NAME, EVENT_SERIAL) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        con.execute_many_iud(SQL, rst)

        for i in range(1500):
            offset=5000
            SQL = """SELECT CASE_SERIAL, SEC_TOPIC, CASE_DATE, CASE_TITLE, CASE_CONTENT, FIRST_TOPIC, CASE_LOCATION,
            CASE_SOURCE FROM TOPIC_ANALYTICS GROUP BY CASE_SERIAL limit {},5000""".format(offset)
            data= con.execute_query(SQL)
            dl = []
            for line in data:
                dl.append(self.Vectorize(content=line[1], location=line[6]))
            train_data = np.array(dl)
            print("prepare data")
            cluster = DBSCAN(eps=0.1, min_samples=2, metric='cosine', n_jobs=-1).fit_predict(X=train_data)
            clsGuid = dict()
            rst = []
            for i in range(len(cluster)):
                id = cluster[i]
                if id != -1:
                    if id not in clsGuid.keys():
                        clsGuid[id] = {}
                        clsGuid[id]['guid'] = str(uuid.uuid1())
                        clsGuid[id]['name'] = str(data[i][1])
                        line = [clsGuid[id]['guid'], str(data[i][0]), str(data[i][2]), str(data[i][3]), str(data[i][4]),
                                str(data[i][5]),str(data[i][1]), str(data[i][6]), clsGuid[id]['name'], clsGuid[id]['guid'],str(data[i][7])]
                        rst.append(line)
                        # print("appended"+str(i))
            SQL = """INSERT INTO EVENT_ANALYSIS_TEMP(ROWGUID, CASE_SERIAL, CASE_DATE, CASE_TITLE, CASE_CONTENT,
            FIRST_TOPIC,SEC_TOPIC,CASE_LOCATION,ANALYSIS_NAME,EVENT_SERIAL,CASE_SOURCE) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)"""
            con.execute_many_iud(SQL, rst)


if __name__ == "__main__":
    model_path = "gen/models/w2v.model"
    eventAna = EventWorker(model_path)
    eventAna.main_dbscan()
