# -*- coding: utf-8 -*-
"""
Entropy difference algorithm for keyword extraction.

"""
import math
import operator
import string
import jieba.posseg as pseg
from .stop_words import english_stop_words
from .chinese_stop_words import chinese_stop_words


def remove_stop(text):
    'Remove stop word'
    return [x for x in text if x not in english_stop_words + [""]]


def clean_words(text):
    'standardization document: Removing punctuation,all letters lower case'
    text = text.replace("\n", " ")
    text = text.replace("\t", " ")
    delEStr = string.punctuation + string.digits + "–|[：+——！，。？、~@#￥%……&*（）]"
    translation = str.maketrans("", "", delEStr)
    text = text.translate(translation)  # Remove punctuation and numbers
    text = text.lower()
    text = text.split(' ')
    return text


# clean Chinese words
def clean_chinese(text_list):
    ret = []
    wordflag = {}
    mc = chinese_stop_words + [""]

    for text in text_list:
        words = pseg.cut(text)

        for word, flag in words:
            if word not in mc:
                ret.append(word)
                if word not in wordflag.keys():
                    wordflag[word] = flag
    return ret, wordflag


def keyword_by_entropydiff(text):
    """
    key word extraction by entropy difference.
    :param text: ['word', 'word', ...] iterable word list
    :return: sorted word dictionary
    """
    l = len(text)
    location = {}
    distance = {}
    for i, word in enumerate(text, 0):
        if word not in location.keys():
            location[word] = i
            distance[word] = [i]
        else:
            distance[word].append(i - location[word])
            location[word] = i
    for word in distance.keys():
        distance[word].append(l - location[word] + distance[word][0])
        distance[word].remove(distance[word][0])

    value = {}
    for word in list(set(text)):
        intrinsic = {}
        extrinsic = {}
        mean = 1.0 * l / len(distance[word])
        # print 'mean:',mean
        for num in distance[word]:
            if num <= mean:
                intrinsic[num] = 1
            else:
                extrinsic[num] = 1
        # print len(intrinsic),len(extrinsic)
        H_dI = math.log(len(intrinsic), 2) if len(intrinsic) != 0 else 0
        H_dE = math.log(len(extrinsic), 2) if len(extrinsic) != 0 else 0
        EDq_d = H_dI ** 2 - H_dE ** 2

        pI = 0
        Hgeo_dI = 0.0
        Hgeo_dE = 0.0
        try:
            for i in range(1, int(mean)):
                pI += (1 / mean) * math.pow(1 - 1 / mean, i - 1)
            for i in range(1, int(mean)):
                Hgeo_dI += -(
                    (1 / mean) * math.pow(1 - 1 / mean, i - 1)) / pI * math.log(
                    ((1 / mean) * math.pow(1 - 1 / mean, i - 1)) / pI, 2)
            pE = 1 - pI
            for i in range(int(mean), l):
                Hgeo_dE += -(
                    (1 / mean) * math.pow(1 - 1 / mean, i - 1)) / pE * math.log(
                    ((1 / mean) * math.pow(1 - 1 / mean, i - 1)) / pE, 2)
            EDgeoq_d = Hgeo_dI ** 2 - Hgeo_dE ** 2
            EDnorq_d = EDq_d / abs(EDgeoq_d) if abs(EDgeoq_d) != 0 else -1000
        except Exception as err:
            EDnorq_d = -1000

        value[word] = EDnorq_d
        # print(word, EDnorq_d)
    # print('Calculate Over...')
    v = sorted(value.items(), key=operator.itemgetter(1), reverse=True)
    return v
