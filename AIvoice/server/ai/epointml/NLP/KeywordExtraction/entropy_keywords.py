# -*- coding:utf-8 -*-
"""
Description:
    通过左右信息熵提取重要关键词

@author: Adrian
@date: 2018/7/9
"""

import jieba.posseg as pseg
from collections import defaultdict, OrderedDict
import numpy as np


def bient_kw(src, minC=6):
    """

    :param src: 语料数据，str格式，可以直接用于分词的那种
    :param minC: 左右词频最小出现次数，用于过滤掉一些出现次数较少的词
    :return: OrderDict - 排序过的dict, wt - 词性标注 dict
    """
    data = list(pseg.cut(src))
    k = len(data)
    wd = dict() # word dict
    wt = defaultdict(None) # word type dict
    for i in range(1, k-1):
        if data[i].word in wd.keys():
            wd[data[i].word][data[i-1].word] += 1
            wd[data[i].word][data[i+1].word] += 1
        else:
            wd[data[i].word] = defaultdict(int)
            wt[data[i].word] = data[i].flag
            wd[data[i].word][data[i-1].word] += 1
            wd[data[i].word][data[i+1].word] += 1

    """
    entrypy: -sum(p * log p)
    """
    dd = defaultdict(int)
    for word in wd.keys():
        dword = wd[word]
        wl = []
        for w in dword:
            wl.append(dword[w])
        n = np.array(wl)
        sum = n.sum()
        if sum > minC:
            ent = 0
            for i in wl:
                ent += - (i/sum) * np.log2(i/sum)
            dd[word] = ent

    orderdict = OrderedDict(sorted(dd.items(), key=lambda t: t[1], reverse=True))
    return orderdict, wt
