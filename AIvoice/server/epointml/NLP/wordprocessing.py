# -*- coding: utf-8 -*-
import jieba
import operator
import codecs

jieba.set_dictionary('lib/dict.txt')
punct = set(u'''1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ''')

stoplist = []
with codecs.open('lib/stop','r', encoding="utf-8") as f:
    lines = f.readlines()
    for word in lines:
        stoplist.append(word.strip())
stopset = set(stoplist)
filterpunt = lambda s: ''.join(filter(lambda  x: x not in punct, s))


def cut_word(sentence):
    seglist = jieba.cut(filterpunt(sentence.replace('\r\n','a')), cut_all=False)

    worddict = {}
    for word in seglist:
        if (word not in stopset) and (len(word) > 1):
            if word in worddict:
                worddict[word] += 1
            else:
                worddict[word] = 1

    sorted_words = sorted(worddict.iteritems(), key=operator.itemgetter(1), reverse=True)
    return sorted_words


if __name__ == "__main__":
    sentence = u"路灯不亮创卫工单：来电人反映：青口镇东关社区东方市场向东200米的垃圾回收站，向南第七、第八盏路灯不亮，影响居民正常生活，希望相关部门及时修复，请核实处理。"

    seglist = cut_word(sentence)
    for item in seglist:
        print(item[0], item[1])