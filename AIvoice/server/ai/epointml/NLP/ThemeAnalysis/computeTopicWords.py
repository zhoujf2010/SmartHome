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
from config.settings import *
import os
from pyltp import Segmentor
from pyltp import Postagger


def bient_kw(src, minC=30):
    """
    :param src: 语料数据，str格式，可以直接用于分词的那种
    :param minC: 左右词频最小出现次数，用于过滤掉一些出现次数较少的词
    :return: OrderDict - 排序过的dict, wt - 词性标注 dict
    """
    cws_model_path = os.path.join(LTPMODEL_PATH, 'cws.model')  # 分词模型路径，模型名称为`cws.model`
    pos_model_path = os.path.join(LTPMODEL_PATH, 'pos.model')  # 词性标模型注模型，模型名称为'pos.model'
    segmentor = Segmentor()  # 初始化分词器实例
    segmentor.load_with_lexicon(cws_model_path, os.path.join(INPUTFILE_PATH, 'lexicon.txt'))  # 加载模型
    postagger = Postagger()  # 初始化词性标注实例
    postagger.load_with_lexicon(pos_model_path, os.path.join(INPUTFILE_PATH, 'wordtag.txt'))  # 加载模型
    words = list(segmentor.segment(src))
    postags = list(postagger.postag(words))

    k = len(words)
    wd = dict() # word dict
    wt = defaultdict(None) # word type dict
    for i in range(1, k-1):
        if words[i] in wd.keys():
            wd[words[i]][words[i-1]] += 1
            wd[words[i]][words[i+1]] += 1
        else:
            wd[words[i]] = defaultdict(int)
            wt[words[i]] = postags[i]
            wd[words[i]][words[i-1]] += 1
            wd[words[i]][words[i+1]] += 1

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
