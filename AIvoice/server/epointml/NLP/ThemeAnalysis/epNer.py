# -*- coding: utf-8 -*-
"""
采用Pyltp处理Ner问题
"""
import re
from pyltp import Segmentor
from pyltp import Postagger
from pyltp import Parser
from .settings import *
import os
import codecs


class Ner(object):
    cws_model_path = os.path.join(LTPMODEL_PATH, 'cws.model')  # 分词模型路径，模型名称为`cws.model`
    pos_model_path = os.path.join(LTPMODEL_PATH, 'pos.model')  # 词性标模型注模型，模型名称为'pos.model'
    par_model_path = os.path.join(LTPMODEL_PATH, 'parser.model')  # 句法解析模型路径，模型名称为'parser.model'

    segmentor = Segmentor()  # 初始化分词器实例
    segmentor.load_with_lexicon(cws_model_path, os.path.join(INPUTFILE_PATH, 'lexicon.txt'))  # 加载模型
    postagger = Postagger()  # 初始化词性标注实例
    postagger.load_with_lexicon(pos_model_path, os.path.join(INPUTFILE_PATH, 'wordtag.txt'))  # 加载模型
    parser = Parser()  # 初始化句法分析实例
    parser.load(par_model_path)  # 加载模型

    # 时间匹配正则式
    time_pattern = re.compile('((\d{4}[-/\.])?\d{1,2}([-/\.]\d{1,2})?\s\d{1,2}:\d{1,2}(:\d{1,2})?'
                         '|(\d{4}[0/\.])?\d{1,2}[-/\.]\d{1,2}|\d{1,2}:\d{1,2}|\d+点(\d+分)?)')
    name_pattern = re.compile('.先生|.女士|叫.{3}')
    # 提取人名依据的句法关系
    rela = ['SBV', 'VOB', 'IOB', 'FOB', 'DBL', 'COO']
    # 屏蔽的时间词后缀
    stop_time_suffix = ['栋', '期', '室']
    # 屏蔽的时间词
    stoptimefile = codecs.open(os.path.join(INPUTFILE_PATH, 'stoptimewords.txt'),'r', encoding='utf-8')
    stoptimelist = [ts.strip() for ts in stoptimefile.readlines()]
    stoptimefile.close()

    def __init__(self):
        # 分词列表
        self.words = []
        # 词性列表
        self.postags = []
        # 词句法分析后的列表
        self.arcs = []
        # 传进来工单的编码
        self.content_encoding = ''

    # 预处理输入工单
    def input(self, casecontent):
        self.casecontent = casecontent
        self.words = list(Ner.segmentor.segment(self.casecontent))
        self.postags = list(Ner.postagger.postag(self.words))
        self.arcs = list(Ner.parser.parse(self.words, self.postags))

    # 抽取地名
    def extract_address(self):
        address = []
        for i in range(0, len(self.postags)):
            if self.postags[i] == 'ns':  # 匹配地名
                if i == 0 or self.postags[i - 1] != 'ns':
                    address.append(self.words[i])
                else:
                    address[len(address) - 1] += self.words[i]
        if len(address) != 0:
            address = list(set(address))  # 地名去重
        else:
            address.append('NULL')
        return '; '.join(address)

    # 抽取时间
    def extract_time(self):
        timecol = []
        for i in range(0, len(self.postags)):
            if self.postags[i] == 'nt' and (i + 1 == len(self.postags) or self.postags[i + 1] != 'wp') \
                    and self.words[i][-1] not in Ner.stop_time_suffix and self.words[i] not in Ner.stoptimelist:  #匹配时间
                if i == 0 or self.postags[i - 1] != 'nt':
                    timecol.append(self.words[i])
                elif len(timecol) != 0:
                    timecol[len(timecol) - 1] += self.words[i]

        # 利用正则提取时间
        timere = Ner.time_pattern.findall(self.casecontent)
        for timeitem in timere:
            timecol.append(timeitem[0])
        if len(timecol) != 0:
            timecol = list(set(timecol))  # 时间去重
        else:
            timecol.append('NULL')
        return '; '.join(timecol)

    #抽取人名
    def extract_peoplename(self):
        peoplename = []
        for i in range(0, len(self.postags)):
            if self.postags[i] == 'nh' and self.arcs[i].relation in Ner.rela:  # 匹配人名
                peoplename.append(self.words[i])

        #利用正则匹配人名
        namere = Ner.name_pattern.findall(self.casecontent)
        for nameitem in namere:
            if nameitem[0] == '叫':
                if nameitem[1:3] in self.words:
                    peoplename.append(nameitem[1:3])
                elif nameitem[1:4] in self.words:
                    peoplename.append(nameitem[1:4])
            else:
                peoplename.append(nameitem)
        if len(peoplename) != 0:
            peoplename = list(set(peoplename))  # 人名去重
        else:
            peoplename.append('NULL')
        return '; '.join(peoplename)

    #抽取机构名
    def extract_institute(self):
        institute = []
        for i in range(0, len(self.postags)):
            if self.postags[i] == 'ni':  # 匹配机构名
                institute.append(self.words[i])
        if len(institute) != 0:
            institute = list(set(institute))  # 机构名去重
        else:
            institute.append('NULL')
        return '; '.join(institute)


if __name__ == '__main__':
    nerins = Ner()
    nerins.input('丁家庄燕升园小区附近工地叫萨比尼斯的施工噪音扰民,叫涂文的话务员于5点23分与市环保局的陈女士进行联系，联系号码为:12369，电话接通。2018/4/7 6:54:答复意见为：已告知。')
    print('time:',nerins.extract_time())
    print('name:',nerins.extract_peoplename())
    print('address:',nerins.extract_address())
    print('institute:',nerins.extract_institute())
