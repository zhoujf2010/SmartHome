# -*- coding: utf-8 -*-
"""
Description: 结巴分词

@author: WangLeAi

@date: 2021/3/3
"""
import jieba
import jieba.posseg as pseg


class JiebaUtil(object):
    def __init__(self, stopset=(), wordtype=('n', 'ns', 'v', 'vn')):
        """
        JiebaUtil初始化

        Parameters
        ----------
        stopset: set
            停用词表，默认为空
        wordtype: set
            词性标注类型，默认n, ns, v, vn
        """
        self._stopset = stopset
        self._wordtype = wordtype

    def loaddict(self, dictpath, stopword, wordtype=('n', 'ns', 'v', 'vn')):
        """
        加载词典, 停用词，词性

        Parameters
        ----------
        dictpath: str
            词典文件的路径.

        stopword: str
            停用词文件的路径.

        wordtype: tuple/list
            词性标注类型，possegcut会过滤剩下wordtype下的词性.
        """
        jieba.load_userdict(dictpath)
        stopwords = set([line.rstrip() for line in open(stopword, encoding='utf8')])
        self._stopset = stopwords
        self._wordtype = wordtype

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
        seg_list = pseg.cut(line)
        words_rst = []
        seg_rst = []
        for w in seg_list:
            if (w.word not in self._stopset) & (w.flag in self._wordtype):
                words_rst.append(w.word)
                seg_rst.append(w.flag)
        return words_rst, seg_rst

    def cut(self, line, cut_all=False):
        """
        普通分词, 只过滤停用词.

        Parameters
        ----------
        line: str
            需要分词的文本数据.
        cut_all: bool
            是否采用全模式分词, 默认为False

        Returns
        -------
        rst: list
            分词结果列表
        """
        seg_list = jieba.cut(line, cut_all=cut_all)
        rst = []
        for w in seg_list:
            if w not in self._stopset:
                rst.append(w)
        return rst


jiebautil = JiebaUtil()
