# -*- coding: utf-8 -*-
from collections import defaultdict
import jieba.posseg as pseg
import json
import os
import pickle
import re
import logging

class WordSlot(object):
    def __init__(self):
        self.logger =  logging.getLogger(__name__)
        self.re_json = None
        self.dict_data_path = "gen/data/dict.txt"

    @staticmethod
    def name():
        raise NotImplementedError

    def predict(self, text):
        raise NotImplementedError

    def load_re_json(self, target_folder):
        with open(os.path.join(target_folder, "word_slot_re.json"), "r", encoding="utf-8") as f:
            self.re_json = json.loads(f.read())


class JieBaPos(WordSlot):
    def __init__(self):
        self.postags = []
        super().__init__()

    def train(self, data):
        print(data)
        my_dict = {}
        with open(self.dict_data_path, "r", encoding="utf-8") as f:
            for i in f.readlines():
                line = i.strip().split(" ")
                k = len(line)
                if k == 3:
                    my_dict[str(line[0])] = "{0} {1}".format(str(line[1]), str(line[2]))
        for d in data:
            if d["target"]:
                slot_json = d["target"]
                for word_slot in slot_json:
                    print(word_slot)
                    word = word_slot["value"]
                    row_guid = word_slot["entity"]
                    my_dict[word] = "10000 {0}".format(row_guid)
                    self.postags.append(row_guid)
        # 标签去重
        self.postags = list(set(self.postags))

        # 更新进词典文件
        with open("gen/models/word_slot_model/dict.txt", "w", encoding="utf-8") as f:
            items = list(my_dict.items())
            for i, j in items:
                line = "{0} {1}\n".format(str(i), j)
                f.write(line)

        with open("gen/models/word_slot_model/postags.pkl", "wb") as f:
            pickle.dump(self.postags, f)

    def init_model(self):
        pseg.initialize("gen/models/word_slot_model/dict.txt")
        with open("gen/models/word_slot_model/postags.pkl", "rb") as f:
            self.postags = pickle.load(f)

    def predict(self, text):
        """
        词性标注方法预测实体
        Parameters
        ----------
        text: str
            实体识别输入文本
        Return
        ------
        {
            "entities": [
                {
                    "start": 0,
                    "end": 4,
                    "value": "Hello",
                    "entity": "cuisine"
                }]
        }
        """
        # print(self.postags)
        wt = pseg.cut(text)
        word_list = list(wt)
        # print(word_list)
        pos_container = defaultdict(list)
        for w in range(len(word_list)):
            if word_list[w].flag in self.postags:
                if w == 0 or word_list[w - 1].flag != word_list[w].flag:
                    pos_container[word_list[w].flag].append(word_list[w].word)
                else:
                    pos_container[word_list[w].flag][len(pos_container[word_list[w].flag]) - 1] += word_list[w].word

        rst = {"entities": []}
        for i, j in pos_container.items():
            el = list(set(j))
            for entity in el:
                start = text.find(entity)
                rst["entities"].append(
                    {"value": entity, "entity": i, "start": start, "end": start + len(entity), "length": len(entity)})
        # print(self.re_json)
        # for j in self.re_json:
        #     for r_l in self.re_json[j]:
        #         value = get_re(text, r_l)
        #         if value:
        #             rst["entities"].append({"value": value, "entity": j})
        return rst

    @staticmethod
    def name():
        return "JieBa"


def get_re(word, re_txt):
    n = re.findall(re_txt, word)
    # print(n)
    if len(n) >= 1:
        return n[0]
    else:
        return False


if __name__ == "__main__":
    a = "123123123123213"
    print(a.find("3124"))
