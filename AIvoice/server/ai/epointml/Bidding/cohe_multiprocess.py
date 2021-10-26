# -*- coding: utf-8 -*-
import multiprocessing
import cohesion as coh
import numpy as np


"""
亲密度算法 webapi 的并行计算实现.
主要功能：
    1. 获取标段报价聚合度列表.
    2. 读取最大进程数, 构建进程池.
    3. 将社区网络分组的计算任务分给不同进程.
    4. 回收各项进程返回数据
Author: Adrian
Date: 2016-12-29
"""


# 单进程计算亲密度
def cohesion_sproc(dwlist,dw_cohesion,groupPack,smcoh,smgau):
    """
    :param dwlist:
    :param dw_cohesion:
    :param groupPack:
        format:
        [{group id : group}, ... ]
    :param sm:
        shared memory - format:
        {
            'cohesion':[],
            'gaussian':[]
        }
    :return:
    """
    for sg in groupPack:
        for groupid in sg:
            cohesion = coh.group_member_intimacy(dwlist,dw_cohesion,sg[groupid])
            # print("group id: ", groupid)
            # print("cohesion is: ", cohesion)
            klen = len(cohesion)
            count_list = []
            for i in range(klen):
                smcoh.append({"GroupID": groupid,
                              "dw1": int(cohesion['dw1'][i]),
                              "dw2": int(cohesion['dw2'][i]),
                              "cohesion": float(cohesion['cohesion'][i]),
                              "count": int(cohesion['count'][i])})
                count_list += [int(cohesion['count'][i])]
            if len(count_list) > 0:
                smgau.append({'GroupID': groupid,
                              'mean': np.mean(count_list),
                              'std': np.std(count_list)})


# parallel programming api
def cohesion_parallel(biaoDuanInfo, dwGroup, proc_num=4):
    """

    :param biaoDuanInfo: 标段信息表
    :param dwGroup:  单位分组
    :param proc_num: 进程数
    :return:
    """

    pool_size = multiprocessing.cpu_count()
    if proc_num < pool_size:
        pool_size = proc_num

    # print("PoolSize is ", pool_size)
    # pool = multiprocessing.Pool(processes=pool_size)

    sManager = multiprocessing.Manager()
    sharedMemCoh = sManager.list() # for non-gaussian distribution
    sharedMemGau = sManager.list()

    # sharedMem = sManager.dict({'cohesion':[],'gaussian':[]}) # for gaussian distribution
    # sharedMem['cohesion'] = []
    # sharedMem['gaussian'] = []

    colst = coh.intimacy_degree(coh.loop_dispersion(biaoDuanInfo))
    grplst = coh.df_to_group(biaoDuanInfo)

    # divide dwGroup by pool_size
    gpack = {}
    klen = len(dwGroup)
    if klen < pool_size:
        pool_size = klen

    print("PoolSize is ", pool_size)

    for i in range(pool_size):
        gpack[i] = []

    # sort dwGroup by value length.
    sorted_dwGroup = sorted(dwGroup.items(), key=lambda item:len(item[1]))

    # divide dwGroup into different pack
    # for i in dwGroup:
    #    gpack[(i % pool_size)].append({i:dwGroup[i]})

    for i in sorted_dwGroup:
        gpack[i[0] % pool_size].append({i[0]:i[1]})

    """
    dwGroup format:
    {
        Group ID1 (int) : Group1(list),
        ...
    }

    gpack format:
    {
        1: [{groupid : group}, ... ]
        2: ...
    }
    """

    pool_process ={}
    for i in range(pool_size):
        pool_process[i] = multiprocessing.Process(target=cohesion_sproc,args=(grplst,colst,gpack[i],sharedMemCoh,sharedMemGau))
        pool_process[i].start()

    for i in range(pool_size):
        pool_process[i].join()

    # print dict(sharedMem)
    rst = {
        "cohesion":list(sharedMemCoh),
        "gaussian":list(sharedMemGau)
    }
    return rst


