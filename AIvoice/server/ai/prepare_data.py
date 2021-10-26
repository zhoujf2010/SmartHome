# -*- coding: utf-8 -*-
from epointml.utils import DbPoolUtil
from nlu.word_slot_model import *
from nlu.intention_model import *


def get_all_classes(model):
    """
    获取父类的所有子类
    """
    all_subclasses = {}
    for subclass in model.__subclasses__():
        if not (subclass.__name__ in all_subclasses.keys()):
            all_subclasses[subclass.name()] = subclass.__name__
        # get_all_classes(subclass)
    return all_subclasses


class PrepareData(object):
    """
    数据准备，生成文件:
        gen/data/action.config
        gen/data/domain.yml
        gen/data/demo-rasa.json
        gen/data/stories.md
    """

    def __init__(self, args):
        self.intent_model = eval(get_all_classes(NaturalLanguageInterpreter)[args["classifier_model"]])()
        self.word_slot_model = eval(get_all_classes(WordSlot)[args["word_slot_model"]])()
        self.__con = DbPoolUtil(jdbcurl=args["jdbcurl"])
        self.args = args

    def intent_train_data(self):
        sql = """select {0}, labeltype from {1} where ifnull({0},'')!='' and ifnull(labeltype,'')!=''""".format(
            self.args["content"], self.args["table"])
        data = self.__con.execute_query(sql, dict_mark=True)
        self.intent_model.train(data)

    def word_slot_train_data(self):
        sql = """select {0}, target from {1} where ifnull({0},'')!='' and ifnull(target,'')!=''""".format(
            self.args["content"], self.args["table"])
        data = self.__con.execute_query(sql, dict_mark=True)
        self.word_slot_model.train(data)


if __name__ == "__main__":
    pass
    # dp = prepareData({"jdbcurl": "jdbc:mysql://192.168.186.13:3306/rasa_zwfw★root★Gepoint"})
    # dp.resolveJson(demojson="gen/data/demo-rasa.json",
    #                ner_train="gen/data/nlu_train/train.txt",
    #                classifier_train="gen/data/classifier_train/train.txt")
    # dp.sql_domain()
