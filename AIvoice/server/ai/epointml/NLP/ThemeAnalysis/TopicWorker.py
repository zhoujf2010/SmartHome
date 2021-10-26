# -*- coding: utf-8 -*-
from config.settings import *
import os
from pyltp import Segmentor, Postagger
import time
import datetime
import uuid
import epNer
import codecs


"""
   @:function 用来计算两个文本的相似度，返回某一个文本的 topoic
   @:parameter:  标准语料集 主题名称 topicName, 主题单词 topicWord ,主题对应的id编号topicNameID  测试  直接一行文本
   @:returns: 返回测试语料集对应的  工单编号  ， topic编号列表
"""
class Jacard:
    def __init__(self, topicName, topicWord, topicNameID=None):
        self.topicName = topicName
        self.topicWord = topicWord
        self.topicNameID = topicNameID

    def getTopicName(self, content):
        max_jacard = 0
        jacard_index = 0
        for index in range(len(self.topicWord)):
            countMerge = 0
            s = set(self.topicWord[index])
            for w in content:
                if w in self.topicWord[index]:
                    countMerge += 1
                s.add(w)
            if countMerge / len(s) > max_jacard:
                max_jacard = countMerge / len(s)
                jacard_index = index
        return self.topicName[jacard_index]


"""
 返回一个预处理每个类型的分词，返回一个 分词后的列表
"""
class WorkPre:
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


class NewWorkorder:
    def __init__(self):
        self.topicName = []
        self.topicWord = []
        self.secKeyWord = []

    # 得到 主题-词（self.topicName-self.topicWord）  和 主题-编号(self.topicName,self.topicNameID)
    def initial(self):
        # 获取一级主题，极其对应的单词-
        f = codecs.open(LDATOPICNAMEMODEL_PATH, 'r', encoding='utf-8')
        lines = f.readlines()
        for line in lines:
            tName = line.split(":")[1].split()[0]
            tempWordList = line.split(":")[1].split()[1:]
            self.topicName.append(tName)
            self.topicWord.append(tempWordList)
        f.close()
        # 读取二级词表
        f = codecs.open(SECKEYWORD_PATH, 'r', encoding='utf-8')
        lines = f.readlines()
        for line in lines:
            self.secKeyWord.append(line.split("\n")[0])
        f.close()

    def getWorkorders(self,workordersPre, ner, segmentor, postagger, content):
        # 读取数据库数据
        workcontent = workordersPre.getCutSetence(segmentor, postagger, content)
        if len(workcontent) > 0:
            # 获取一级主题
            first_topic = Jacard(self.topicName, self.topicWord).getTopicName(workcontent)
            # 获取二级关键词
            sec_topic = ";".join(list(set([w for w in workcontent if w in self.secKeyWord])))
            if sec_topic is None:
                sec_topic = workcontent[0]
            ner.input(content.encode("utf-8"))
            return first_topic,sec_topic,ner.extract_address()
        segmentor.release()  # 释放分词模型
        postagger.release()  # 释放词性标注模型


