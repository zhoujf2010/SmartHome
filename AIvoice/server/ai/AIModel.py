
from ai.word_slot_model import *
from ai.intention_model import *
from flask import request
import traceback
import shutil
import asyncio
from webFrame.baseview import BaseView, route

logger = logging.getLogger(__name__)



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

    
async def async_setup(app, rootPath):
    view = AIModel(app,rootPath)
    app.register_view(view)
    app.loop.run_in_executor(None, view.loadModel)

    async def dataReceive(eventtype, data):  #收到角度变换数据
        cmd = view.doPredict(data)

        intenttype = cmd["intent"]["name"]
        intentname = view.getIntentTypes()[intenttype]
        dt = [cmd["text"],intenttype,intentname]
        for item in cmd["entities"]:
            entitytype = item["entity"]
            entityname = view.getEntityTypes()[entitytype]
            dt.append([entitytype,entityname])

        return await app.eventBus.async_fire("cmd",dt)

    app.eventBus.async_listen("oracmd", dataReceive)

    def onconfigchange(eventtype, data):
        logger.info("收到配置变化")
        view.clearCache()

    app.eventBus.async_listen("configchange", onconfigchange)
    


class AIModel(BaseView):
    name = "AIView"

    def __init__(self,app,rootPath) -> None:
        import tensorflow.compat.v1 as tf
        tf.disable_v2_behavior()
        self.rootPath = rootPath
        self.app = app

    def getEntityTypes(self):
        #获取实体类别表
        if not hasattr(self,"EntityTypes"):
            f = open('./data/entityTypes.json','r',encoding="utf-8")
            data = f.read()
            data = json.loads(data)
            f.close()
            EntityTypes = {}
            for item in data:
                EntityTypes[item["id"]] = item["text"]
            self.EntityTypes = EntityTypes
        return self.EntityTypes

    def getIntentTypes(self):
        #获取意图表
        if not hasattr(self,"IntentTypes"):
            f = open('./data/intentTypes.json','r',encoding="utf-8")
            data = f.read()
            data = json.loads(data)
            f.close()
            IntentTypes = {}
            for item in data:
                IntentTypes[item["id"]] = item["text"]
            self.IntentTypes = IntentTypes
        return self.IntentTypes

    def clearCache(self):
        if hasattr(self,"IntentTypes"):
            del self.IntentTypes
        if hasattr(self,"EntityTypes"):
            del self.EntityTypes

    @route("/train", methods=['POST'])
    async def train(self, request):
        if os.path.exists("gen/graph"):
            os.remove("gen/graph")
        if os.path.exists("gen/models/intent_model"):
            shutil.rmtree("gen/models/intent_model")
        if os.path.exists("gen/models/word_slot_model"):
            shutil.rmtree("gen/models/word_slot_model")
        os.makedirs("gen/models/intent_model")
        os.makedirs("gen/models/word_slot_model")

        
        #意图训练
        self.intent_model = eval(get_all_classes(NaturalLanguageInterpreter)["Bert"])()
        f = open('./data/intent.json','r',encoding="utf-8")
        data = f.read()
        data = json.loads(data)
        f.close()
        self.intent_model.train(data)

        #词槽训练
        self.word_slot_model = eval(get_all_classes(WordSlot)["JieBa"])()
        f = open('./data/slot.json','r',encoding="utf-8")
        data = f.read()
        data = json.loads(data)
        f.close()

        self.word_slot_model.train(data)
        logger.info("训练完成")

    def loadModel(self):
        logger.info("模型开始加载")
        self.word_slot_model = eval(get_all_classes(WordSlot)["JieBa"])()
        self.word_slot_model.init_model()
        self.intent_model = eval(get_all_classes(NaturalLanguageInterpreter)["Bert"])(
            self.word_slot_model)
        self.intent_model.init_model()
        logger.info("模型加载完成")

    def doPredict(self,text):
        return self.intent_model.parse(text)

    @route("/api/predict", methods=['POST'])
    async def predict(self, request):
        json_data = await request.json()
        try:
            if "text" in json_data:
                ret = {'code': '1', 'result': self.intent_model.parse(json_data["text"])}
            else:
                ret = {"code": '0', "result": "存在异常，请传入正确参数"}
        except Exception as e:
            ret = {"code": "0", "result": "存在异常" + str(e)}
            logger.error("异常信息:")
            logger.error(traceback.print_exc())
        return json.dumps(ret, ensure_ascii=False)
    