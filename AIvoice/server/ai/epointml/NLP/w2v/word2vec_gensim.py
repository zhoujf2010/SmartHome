# -*- coding: utf-8 -*-
import gensim
import jieba.posseg as pseg
import jieba.analyse
from sklearn.cluster import KMeans
import codecs
from gensim.models.phrases import Phrases
import os
import uuid
import re

stopset = []
wordtype = ['n', 'ns', 'v', 'vn']
def cut_word(s):
    """
    分词, 可在此加入POS过滤词方案
    :param s:
    :return:
    """
    sgen = jieba.cut(s, cut_all=True)
    #sgen = pseg.cut(filterpunt(s))
    rst = []
    for w in sgen:
        # print(w.word, w.flag)
        if (w.word not in stopset) & (len(w.word) > 1) & (w.flag in wordtype):
            rst.append(w.word)
    return rst


def w2v(data=None, model_loc='gen/models/w2v.model'):
    """
    WordEmbedding
    :param
        data: sentence list/tuple. [sentence, sentence, ...]
        model_loc: model location
    :return: save w2v.model
    """
    if data is None:
        with open('gen/small_train.txt', 'r') as f:
            data = f.readlines()
    sentence = list()
    for i in range(len(data)):
        try:
            sentence.append([j for j in jieba.cut(data[i], cut_all=False)])
            # sentence.append(cut_word(data[i]))
        except:
            continue
    # bigram 处理原始数据
    # bigram = Phrases(sentences=sentence)
    # co_sentences = [bigram[i] for i in sentence]
    co_sentences = sentence

    f_s = []
    # 过滤停用词
    for se in co_sentences:
        line = []
        for word in se:
            if (word not in stopset) & (len(word) > 1):
                line.append(word)
        if len(line) > 0:
            f_s.append(line)
    model = gensim.models.Word2Vec(sentences=f_s, sg=1, size=200, window=5, min_count=3, hs=1, workers=7, iter=100)
    model.save(model_loc)


def w2v_related_model(center_word, model_loc='gen/models/w2v.model', topK=20):
    """
    get related words by center word
    :param model_loc: model location
    :param center_word: center word
    :param topK: return topK word
    :return:
    """
    model = gensim.models.Word2Vec.load(model_loc)
    # print("输入词： {0}".format(str(center_word)))

    r = model.wv.most_similar([str(center_word)], topn=topK)
    ret = [{'value': str(i[0])} for i in r]
    return ret


def w2v_related(center_word, model, topK=20):
    """
    get related words by center word
    :param model: model location
    :param center_word: center word
    :param topK: return topK word
    :return:
    """
    # print("输入词： {0}".format(str(center_word)))

    r = model.wv.most_similar([str(center_word)], topn=topK)
    ret = [{'value': str(i[0])} for i in r]
    return ret


def w2v_kmeans(num_c=2000, model_loc='data/models/w2v.model', dst='kcluster.txt'):
    """
    Use kmeans for clustering word vectors.
    :param num_c: Num of clusters
    :param model_loc: Word embedding model location
    :param dst: clustering result saving location
    :return:
    """
    model = gensim.models.Word2Vec.load(model_loc)
    word_vectors = model.wv.syn0
    kmeans_clustering = KMeans(n_clusters=num_c, random_state=0)
    idx = kmeans_clustering.fit_predict(word_vectors)
    # print(word_vectors)
    # print(model.wv.index2word)
    # print(idx)
    word_centroid_map = dict(zip(model.wv.index2word, idx))
    # print(word_centroid_map)

    with codecs.open(dst, 'w', encoding='utf-8') as f:
        for cluster in range(num_c):
            # print('\nCluster: {}'.format(cluster))
            words = list()
            values = list(word_centroid_map.values())
            keys = list(word_centroid_map.keys())
            for i in range(len(word_centroid_map.values())):
                if (values[i] == cluster):
                    words.append(keys[i])
            # print(words)
            line = 'Cluster: {0}\t{1}\n'.format(cluster, words)
            f.write(line)

    # print(kmeans_clustering.labels_)
    # print(kmeans_clustering.cluster_centers_)


def check_alphabet(str):
    my_re = re.compile(r'[A-Za-z]', re.S)
    res = re.findall(my_re, str)
    if len(res):
        return True
    else:
        return False


def na_checker(word):
    return any(c.isdigit() | check_alphabet(c) for c in word)

