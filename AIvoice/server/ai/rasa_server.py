# -*- coding: utf-8 -*-
from prepare_data import *
import json
from flask import request
import traceback


class RASAServer(object):

    def __init__(self, args, logger):
        """
        rasa 模型服务初始化
        Parameters
        ----------
        args: dict
            deploy 步骤传入的参数
        """
        self.logger = logger
        self.word_slot_model = eval(get_all_classes(WordSlot)[args["word_slot_model"]])()
        self.word_slot_model.init_model()
        self.intent_model = eval(get_all_classes(NaturalLanguageInterpreter)[args["classifier_model"]])(
            self.word_slot_model)
        self.intent_model.init_model()

    @staticmethod
    def api_check():
        """
        get请求，用于验证服务是否正常运行
        """
        return "OK"

    def api_predict(self):
        """
        功能：输入文本，和数据库字段相比对，输出大于confidence阈值，个数为number的结果
        text: 待比对字符串
        :return: 符合条件的相似数据
        """
        json_data = json.loads(request.data)#, encoding='utf-8')
        try:
            if "text" in json_data:
                ret = {'code': '1', 'result': self.intent_model.parse(json_data["text"])}
            else:
                ret = {"code": '0', "result": "存在异常，请传入正确参数"}
        except Exception as e:
            ret = {"code": "0", "result": "存在异常" + str(e)}
            self.logger.error("异常信息:")
            self.logger.error(traceback.print_exc())
        return json.dumps(ret, ensure_ascii=False)
