# -*- coding: utf-8 -*-
"""
单位标段报价聚合度算法

输入数据格式JSON
{
    "BiaoDuanInfo": [
        {"BiaoDuanID": 0, "DanWeiID":0, "TouBiaoJinE": 100.2},
		{"BiaoDuanID": 0, "DanWeiID":1, "TouBiaoJinE":100.2},
		{"BiaoDuanID": 1, "DanWeiID":2, "TouBiaoJinE":100.2}
    ]
}

返回数据格式JSON
{
	"JuHeD":[
		{"BiaoDuanID":0, "TouBNum":1. "JuHeD": 87%},
		{"BiaoDuanID":1, "TouBNum":1. "JuHeD": 87%},
		{"BiaoDuanID":2, "TouBNum":1. "JuHeD": 87%}
	]
}

亲密度I 计算公式:
if r <= 1:
    I = (1 - r) * 100
else:
    I = 0

"""

import numpy as np
import pandas as pd


def read_BiaoDuanInfo(infolst):
    klen = len(infolst)
    rst = []
    for i in range(klen):
        rst.append((infolst[i]["BiaoDuanID"],
                    infolst[i]["DanWeiID"],
                    infolst[i]["TouBiaoJinE"]))
    return pd.DataFrame(rst, columns=('BiaoDuanID','DanWeiID','TouBiaoJinE'))


def r_dispersion(input_list):  # 计算报价聚合度
    rst_mean = np.mean(input_list)
    if rst_mean == 0.0:
        return 1
    else:
        return (1-np.std(input_list)/rst_mean)*100  # 返回list的聚合度


def loop_dispersion(df):  # 遍历计算所有聚合度
    klen = len(df)
    temp_bid = []
    rtn_juhe = []
    for i in range(klen):
        if i == 0:
            temp_bid.append(float(df['TouBiaoJinE'][i]))
        elif df['BiaoDuanID'][i] == df['BiaoDuanID'][i-1]:
            try:
                temp_bid.append(float(df['TouBiaoJinE'][i]))
            except Exception as err:
                print(err)
        else:
            try:
                rtn_juhe.append({"BiaoDuanID": int(df['BiaoDuanID'][i-1]),
                                 "TouBNum": len(temp_bid),
                                 "JuHeD": float(r_dispersion(temp_bid))})
                temp_bid = [float(df['TouBiaoJinE'][i])]
            except Exception as err:
                print(err)
    rtn_juhe.append({'BiaoDuanID': int(df['BiaoDuanID'][klen-1]),
                     "TouBNum": len(temp_bid),
                     "JuHeD": float(r_dispersion(temp_bid))})
    return rtn_juhe



