
from ai.word_slot_model import *
from ai.intention_model import *
from flask import request
import traceback
import shutil

import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()

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

class AIModel():
    def __init__(self,rootPath) -> None:
        self.rootPath = rootPath

    def train(self):

        if os.path.exists("gen/graph"):
            os.remove("gen/graph")
        if os.path.exists("gen/models/intent_model"):
            shutil.rmtree("gen/models/intent_model")
        if os.path.exists("gen/models/word_slot_model"):
            shutil.rmtree("gen/models/word_slot_model")
        os.makedirs("gen/models/intent_model")
        os.makedirs("gen/models/word_slot_model")

        
        #意图训练
        self.word_slot_model = eval(get_all_classes(WordSlot)["JieBa"])()
        f = open('./data/intent.json','r')
        data = f.read()
        data = json.loads(data)
        f.close()
        self.intent_model.train(data)

        #词槽训练
        self.intent_model = eval(get_all_classes(NaturalLanguageInterpreter)["Bert"])()
        f = open('./data/slot.json','r')
        data = f.read()
        data = json.loads(data)
        f.close()

        self.word_slot_model.train(data)

    def loadModel(self):

        self.word_slot_model = eval(get_all_classes(WordSlot)["JieBa"])()
        self.word_slot_model.init_model()
        self.intent_model = eval(get_all_classes(NaturalLanguageInterpreter)["Bert"])(
            self.word_slot_model)
        self.intent_model.init_model()


    def predict(self):
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
    