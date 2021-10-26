# coding:utf-8
"""
 返回一个预处理每个类型的分词，返回一个 分词后的列表
"""

from .settings import *


class Workorder:
    def __init__(self):
        self.stopWord = []
        self.sameWord = []

    #  获取停用词
    def getStopWord(self):
        f = open(STOPWORD_PATH, "r" )
        lines = f.readlines()
        for line in lines:
            word = line.split("\n")[0]
            if len(word) == 0:
                continue
            if word not in self.stopWord:
                self.stopWord.append(word)
        f.close()

    # 获取同义词表
    def getSameWord(self):
        f = open(SAMEWORD_PATH, "r" )
        lines = f.readlines()
        for line in lines:
            self.sameWord.append(line.split())

    def initial(self):
        self.getSameWord()
        self.getStopWord()

    # 对每句话进行分词
    def getCutSetence(self, segmentor, postagger, setence):
        #setence = setence.encode('utf-8')
        words = list(segmentor.segment(setence.encode('utf-8')))
        # 将单词进行词性标注
        postags = list(postagger.postag(words))  # 词性标注
        #  这样words中每个单词对应一个词性
        keys = ['i', 'j', 'n', 'ni', 'nz', 'v']  # 成语、缩写、名词、组织、其他名词、动词
        workcontent = []
        for i in range(len(postags)):
            if postags[i] in keys:
                if words[i] not in self.stopWord:  # 去除停用词
                    flag = True
                    for same in self.sameWord:  # 找同义词替换成第一个
                        if words[i] in same:
                            workcontent.append(same[0])
                            flag = False
                            break
                    if flag:
                        workcontent.append(words[i])
        return workcontent
