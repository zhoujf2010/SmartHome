# -*- coding: utf-8 -*-

"""
Biding documents similarity checker. Basically this checker calculate
the index cosine similarity between all sentences between two biding
documents. It also indicates all similar sentence which cosine
similarity over a threshold value. (Maybe 0.7)

Designer: Adrian
Date: Aug 17, 2017
"""
import re
import jieba
import numpy as np
from gensim import corpora, models, similarities


class SamChecker(object):

    def __init__(self, config_file):
        params_config = config_file
        self.hs = float(params_config["highs"])
        self.ms = float(params_config["mins"])
        self.fluctuation = int(params_config["fluctuation"])
        self.sentence_reg = re.compile(u'([,，.。?？!！;；\s]+)')
        self.words_regex = re.compile(u'[^\u4e00-\u9fa50-9a-zA-Z]+')
        self.dictionary = None

    def bag_of_words(self, doc):
        """
        对文本分词
        :param doc: 文本
        :return:
        """
        texts = []
        for line in self.sentence_reg.split(doc):
            line = self.words_regex.sub('', line)
            if line:
                texts.append([i for i in jieba.cut(line)])
        return texts

    def corpora_dictionary(self, docs):
        """
        在计算相似度前必须先生成字典
        :param docs: 文本集合
        :return:
        """
        texts = []
        for doc in docs:
            texts += self.bag_of_words(doc)
        self.dictionary = corpora.Dictionary(texts)

    def calculate_similarity(self, one, two):
        """
        计算相似度
        :param one: 文本1
        :param two: 文本2
        :return:
        """
        corpus = []
        txt_one = self.bag_of_words(one)
        txt_two = self.bag_of_words(two)
        # for line in txt_one:
        #     corpus.append(self.dictionary.doc2bow(line))
        # 文本2作为被对比内容
        for line in txt_two:
            # print self.dictionary.doc2bow(line)
            corpus.append(self.dictionary.doc2bow(line))

        lsi = models.LsiModel(corpus=corpus, id2word=self.dictionary, num_topics=1024)
        # lsi.save('data/lsiModel')

        # 相似矩阵
        index = similarities.MatrixSimilarity(lsi[corpus])
        # index.save('data/lsi.index')

        na, nb = len(txt_one), len(txt_two)
        nm = 0.
        # 置信相似句子、可疑相似句子
        hs_list, ms_list = {}, {}
        ac = 0
        for line in txt_one:
            ac += 1
            vec_bow = self.dictionary.doc2bow(line)
            vec_lsi = lsi[vec_bow]
            # 取与所有句子的相似度并排序
            sims = index[vec_lsi]
            sims = sorted(enumerate(sims), key=lambda item: -item[1])
            for i in range(len(sims)):
                if sims[i][1] < self.ms:
                    break
                # 每句仅与在波动范围内的句子对比
                if np.abs(ac - sims[i][0] - 1) <= self.fluctuation:
                    if sims[i][1] > self.hs:
                        if ac in hs_list:
                            hs_list[ac].append(((sims[i][0] + 1), sims[i][1]))
                        else:
                            hs_list[ac] = [((sims[i][0] + 1), sims[i][1])]
                    elif sims[i][1] > self.ms:
                        if ac in ms_list:
                            ms_list[ac].append(((sims[i][0] + 1), sims[i][1]))
                        else:
                            ms_list[ac] = [((sims[i][0] + 1), sims[i][1])]
            if ac in hs_list:
                nm += 1.
            elif ac in ms_list:
                nm += 0.5
        similarity = 0 if na == 0 or nb == 0 else np.sqrt((nm * nm) / (na * nb))
        return similarity, hs_list, ms_list

    def orginal_texts(self, hs_list, ms_list, doc1, doc2):
        """
        将原文本进行标注，写得这么麻烦就是怕有连续符号导致断句为空，而空字符串又是不适合送入识别相似度的
        :param hs_list: 置信相似句子
        :param ms_list: 可疑相似句子
        :param doc1: 文本1
        :param doc2: 文本2
        :return:
        """
        doc1_sim, doc2_sim = self.__create_simlist(hs_list, ms_list)
        article1 = self.__create_doc(doc1, doc1_sim)
        article2 = self.__create_doc(doc2, doc2_sim)
        return article1, article2

    def __create_simlist(self, hs_list, ms_list):
        """
        获取排序后的相似句子字典,1标识可疑相似句子，2标识置信相似句子
        :param hs_list:
        :param ms_list:
        :return:
        """
        doc1_sim = {}
        doc2_sim = {}
        self.__traverse2_dict(doc1_sim, doc2_sim, hs_list, 2)
        self.__traverse2_dict(doc1_sim, doc2_sim, ms_list, 1)
        return doc1_sim, doc2_sim

    @staticmethod
    def __traverse2_dict(doc1_sim, doc2_sim, sim_list, mark):
        """
        简单点的标注
        :param doc1_sim:
        :param doc2_sim:
        :param sim_list: 相似度字典
        :param mark: 1标识可疑相似句子，2标识置信相似句子
        :return:
        """
        for key1, value1 in sim_list.items():
            if key1 not in doc1_sim:
                doc1_sim[key1] = mark
            for item in value1:
                if item[0] not in doc2_sim:
                    doc2_sim[item[0]] = mark

    @staticmethod
    def __traverse_dict(doc1_sim, doc2_sim, sim_list):
        """
        遍历相似度字典，目前不用，简单点，标注的方式简单点
        :param doc1_sim:
        :param doc2_sim:
        :param sim_list: 相似度字典
        :return:
        """
        for key1, value1 in sim_list.items():
            for item in value1:
                if key1 in doc1_sim:
                    doc1_sim[key1].append(item)
                else:
                    doc1_sim[key1] = [item]
                if item[0] in doc2_sim:
                    doc2_sim[item[0]].append((key1, item[1]))
                else:
                    doc2_sim[item[0]] = [(key1, item[1])]

    def __create_doc(self, doc, doc_sim):
        """
        标注文本
        :param doc: 文本
        :param doc_sim: 文本相似句子字典
        :return:
        """
        # 文章
        article = []
        ori_texts = self.sentence_reg.split(doc)
        ori_texts.append("")
        # 第几句
        index = 0
        for i in range(0, len(ori_texts), 2):
            article.append({"text": ori_texts[i] + ori_texts[i + 1], "mark": 0})
            if ori_texts[i]:
                index += 1
                if index in doc_sim.keys():
                    article[-1]["mark"] = doc_sim[index]
        return article


sam = SamChecker()
