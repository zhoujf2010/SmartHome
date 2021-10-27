# -*- coding:utf-8 -*-
"""
Description: 百度Lac分词模型

不支持jieba形式的自定义字典，主要原因在于他一行是一个短语，可以对短语多个部分分别标注，涉及到最长匹配

意味着如下形式的自定义字典在匹配到花开时返回 花/n 开/v  匹配到花朵时返回花/v 开/n
花/n 开/v
花/v

@author: WangLeAi

@date: 2019/5/6
"""

from LAC import LAC


class LacUtil(object):
    def __init__(self, stopset=(), wordtype=('n', 'ns', 'v', 'vn')):
        """
        lac分词初始化

        Parameters
        ----------
        stopset: set
            停用词表，默认为空
        wordtype: set
            词性标注类型，默认n, ns, v, vn
        """
        self.lac = LAC(mode='lac')
        self._stop_words = stopset
        self._word_type = wordtype

    def loaddict(self, dictpath, stopword, wordtype=('n', 'ns', 'v', 'vn')):
        """
        加载自定义词典, 停用词，词性

        Parameters
        ----------
        dictpath: str
            词典文件的路径.
        stopword: str
            停用词文件的路径.
        wordtype: tuple/list
            词性标注类型，possegcut会过滤剩下wordtype下的词性.
        """
        self.lac.load_customization(dictpath)
        stopwords = set([line.rstrip() for line in open(stopword, encoding='utf8')])
        self._stop_words = stopwords
        self._word_type = wordtype

    def possegcut(self, line):
        """
        词性标注分词, 过滤词性.

        Parameters
        ----------
        line: str
            需要分词的文本数据.

        Returns
        -------
        rst: list
            分词结果列表
        """
        words_rst, seg_rst = self.possegcut_com(line)
        return words_rst

    def possegcut_com(self, line):
        """
        词性标注分词, 过滤词性.

        Parameters
        ----------
        line: str
            需要分词的文本数据.

        Returns
        -------
        rst: list
            分词结果列表
        """
        lac_result = self.lac.run(line)
        words_list = lac_result[0]
        seg_list = lac_result[1]
        words_rst = []
        seg_rst = []
        for i in range(len(words_list)):
            if (words_list[i] not in self._stop_words) & (seg_list[i] in self._word_type):
                words_rst.append(words_list[i])
                seg_rst.append(seg_list[i])
        return words_rst, seg_rst

    def cut(self, line):
        """
        普通分词, 只过滤停用词.

        Parameters
        ----------
        line: str
            需要分词的文本数据.

        Returns
        -------
        rst: list
            分词结果列表
        """
        lac_result = self.lac.run(line)
        rst = []
        for w in lac_result[0]:
            if w not in self._stop_words:
                rst.append(w)
        return rst


lac_util = LacUtil()
