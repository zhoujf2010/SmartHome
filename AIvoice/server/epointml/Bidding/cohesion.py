# -*- coding: utf-8 -*-
"""
亲密度算法 for web api
Author: Adrian
Data: 2016-12-29
"""
import pandas as pd
import numpy as np

"""
常量定义
"""
bd_num = 0  # 标段在csv中第7列
dw_num = 1  # 单位在csv中第8列
bid_num = 2  # 报价在csv中第3列


def clean_data(df):  # 数据清洗
    return df.fillna(value=0)  # 将NaN值转换为0


def r_dispersion(input_list):  # 计算离散系数 r
    rst_mean = np.mean(input_list)
    if rst_mean == 0.0:
        return 0
    else:
        return np.std(input_list) / rst_mean  # 返回list的离散系数


def loop_dispersion(df):  # 遍历计算所有离散系数
    df = clean_data(df)
    k = len(df)
    bid = []
    dis_rst = []
    bd_id = 0
    for i in range(k):
        if i == 0:
            bid.append(float(df.iloc[i, bid_num]))
            bd_id = df.iloc[i, bd_num]
        elif bd_id == df.iloc[i, bd_num]:
            try:
                bid.append(float(df.iloc[i, bid_num]))
            except Exception as err:
                print(err)
                print(i)
        else:
            try:
                dis_rst.append(r_dispersion(bid))
                bid = [float(df.iloc[i, bid_num])]
                bd_id = df.iloc[i, bd_num]
            except Exception as err:
                print(err)
                print(i)
    dis_rst.append(r_dispersion(bid)) # 最后一个离散值
    return pd.Series(dis_rst)  # 返回一个自增长的离散系数列表


def intimacy_degree(df_dispersion):  # 根据离散系数r 计算标段内公司亲密度
    intimacy_list = []
    for i in df_dispersion:
        if i <= 1.:
            intimacy_list.append(100 * (1 - i))  # 亲密度计算公式，可调整
        else:
            intimacy_list.append(0)
    # print pd.Series(intimacy_list)
    return pd.Series(intimacy_list)  # 返回一个自增长的亲密度列表


# helper function: 将biaoDuanId, danWeiId 中BD相同的单位放进同一group
def df_to_group(df):
    k = len(df)
    dw_group = {}
    temp_group = []
    for i in range(k):
        if i == 0:
            temp_group.append(df.iloc[i, dw_num])
        elif df.iloc[i, bd_num] == df.iloc[i - 1, bd_num]:
            temp_group.append(df.iloc[i, dw_num])
        else:
            dw_group[df.iloc[i - 1, bd_num]] = temp_group
            temp_group = [df.iloc[i, dw_num]]
    dw_group[df.iloc[k-1,bd_num]] = temp_group
    # print dw_group
    return dw_group  # 返回一个以标段开头的字典索引(单位)


"""
# 遍历标段，计算出单位之间亲密度， 设置一个单位阈值，计算阈值之内的单位亲密度
def calculate_intimacy_degree(dw_group, df_intimacy, max_dw):
    count = 0
    total_intimacy = 0
    rst_list = []
    for dw1 in range(1, max_dw):
        for dw2 in range(dw1 + 1, max_dw + 1):
            for each_group in dw_group:
                try:
                    if ((dw1 in dw_group[each_group]) & (dw2 in dw_group[each_group])):
                        total_intimacy += df_intimacy.iloc[each_group]
                        count += 1
                except  Exception as err:
                    print err
                    print dw1, dw2, dw_group[each_group]
            try:
                if count == 0:  # 单位之间没有共同投标
                    rst_list.append([dw1, dw2, 0])
                    count, total_intimacy = 0, 0  # count, total 清零
                else:
                    rst_list.append([dw1, dw2, total_intimacy / count])
                    count, total_intimacy = 0, 0  # count, total 清零
            except  Exception as err:
                print err
    return pd.DataFrame(rst_list, columns=['dw1', 'dw2', 'intimacy'])
"""


# 优化亲密度计算算法，计算输入组成员亲密度
def group_member_intimacy(dw_group, df_intimacy, dw_list):  # dw_list
    count = 0
    total_intimacy = 0
    rst_list = []
    dw_length = len(dw_list)  # dw_list length shoud at least 1.
    for dw1 in range(dw_length - 1):
        for dw2 in range(dw1 + 1, dw_length):
            for each_group in dw_group:
                try:
                    if (dw_list[dw1] in dw_group[each_group]) & (dw_list[dw2] in dw_group[each_group]):
                        # print int(each_group), df_intimacy.iloc[int(each_group)]
                        total_intimacy += df_intimacy.iloc[int(each_group)]
                        count += 1
                except Exception as err:
                    print(err)
                    # print dw_list[dw1], dw_list[dw2], dw_group[each_group]
            try:
                if count == 0:
                    rst_list.append([dw_list[dw1], dw_list[dw2], 0, 0])
                    count, total_intimacy = 0, 0
                else:
                    rst_list.append([dw_list[dw1],dw_list[dw2],
                                     total_intimacy/count, count])
                    count, total_intimacy = 0, 0
            except Exception as err:
                print(err)
    return pd.DataFrame(rst_list, columns=('dw1', 'dw2', 'cohesion', 'count'))


"""
# calculate cohesion value between danwei group members.
def get_member_inti(BiaoDuanInfo, DanWeiGroup):

    # :param BiaoDuanInfo: BiaoDuanInfo is data frame structure that includes bdid, dwid, and JinE
    # :param DanWeiGroup: DanWeiGroup includes all danwei that would be used for cohesion calculation.
    # :return: rtn_dwGroup. rtn_dwGroup is a list structure that includes dw1, dw2 and their cohesion.

    df_rst = loop_dispersion(BiaoDuanInfo)
    dw_intimacy = intimacy_degree(df_rst)
    dw_group = df_to_group(BiaoDuanInfo)
    rtn_dwgroup = []

    for singleGroup in DanWeiGroup:
        cohesion = group_member_intimacy(dw_group, dw_intimacy, singleGroup)
        klen = len(cohesion)
        for i in range(klen):
            # print cohesion['dw1'][i]
            rtn_dwgroup.append({"dw1":int(cohesion['dw1'][i]),
                                "dw2":int(cohesion['dw2'][i]),
                                "cohesion":float(cohesion['cohesion'][i]),
                                "count":int(cohesion['count'][i])})

    # add Group ID, std, mean here, for Gaussian distribution
    return rtn_dwgroup
"""


# calculate cohesion value between danwei group members.
# This function includes manipulation on GroupID, so this is for Gaussian distribution
# result only.
def get_member_init(BiaoDuanInfo, DanWeiGroup):
    # The DanWeiGroup should use data structure generated from get_DanWeiGroup_andID
    df_rst = loop_dispersion(BiaoDuanInfo)
    dw_intimacy = intimacy_degree(df_rst)
    dw_group = df_to_group(BiaoDuanInfo)
    rtn_dwGroup = {'cohesion': [], 'gaussian': []}

    for GroupID in DanWeiGroup:
        cohesion = group_member_intimacy(dw_group, dw_intimacy, DanWeiGroup[GroupID])
        klen = len(cohesion)
        count_list = []  # for calculating mean, std, variance - needed by gaussian distribution
        for i in range(klen):
            rtn_dwGroup['cohesion'].append({'GroupID': GroupID,
                                            'dw1': int(cohesion['dw1'][i]),
                                            'dw2': int(cohesion['dw2'][i]),
                                            'cohesion': float(cohesion['cohesion'][i]),
                                            'count': int(cohesion['count'][i])})
            count_list.append(int(cohesion['count'][i]))
        if len(count_list) > 0:
            rtn_dwGroup['gaussian'].append({'GroupID': GroupID,
                                            'mean': np.mean(count_list),
                                            'std': np.std(count_list)})
    return rtn_dwGroup


# 从传递的JSON参数中取得 BiaoDuanInfo信息
def get_BiaoDuanInfo(json_data):
    cnt = json_data["BiaoDuanInfo"]
    df = []
    for item in cnt:
        df.append((item['BiaoDuanID'], item['DanWeiID'], item['TouBiaoJinE']))
    return pd.DataFrame(df,columns=('BiaoDuanID', 'DanWeiID', 'TouBiaoJinE'))


# 从传递的JSON数据中取得DanWeiGroup.
def get_DanWeiGroup(json_data):
    cnt = json_data['DanWei']
    gid = 0
    tempGroup = []
    rtnGroup = []
    klen = len(cnt)
    for i in range(klen):
        if i == 0:
            gid = cnt[i]['GroupID']
            tempGroup.append(cnt[i]['Node'])
        elif cnt[i]['GroupID'] == gid:
            tempGroup.append(cnt[i]['Node'])
        else:
            rtnGroup.append(tempGroup)
            tempGroup = [cnt[i]['Node']]
            gid = cnt[i]['GroupID']
    rtnGroup.append(tempGroup)
    return rtnGroup


# 不仅从JSON数据中获取DanWeiGroup, 同时取得GroupID
def get_DanWeiGroup_andID(json_data):
    cnt = json_data['DanWei']
    rtnGroup = {}
    klen = len(cnt)
    for i in range(klen):
        if cnt[i]['GroupID'] in rtnGroup:
            rtnGroup[cnt[i]['GroupID']].append(cnt[i]['Node'])
        else:
            rtnGroup[cnt[i]['GroupID']]=[cnt[i]['Node']]
    return rtnGroup

"""
rtnGroup format:
{
    # GroupID : Group,
    1:[1,2,3,4],
    2:[5,6,7,8]
}
"""

















