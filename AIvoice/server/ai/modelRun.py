# -*- coding: utf-8 -*-
import os
from epointml.utils import commonUtil, elog

import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()


def init(args):
    """
    初始化阶段
    :param args: 步骤对应的全部参数
    :return:
    """

    if not os.path.exists("logs"):
        os.mkdir("logs")
    commonUtil.setRootPath(os.path.split(os.path.realpath(__file__))[0])
    commonUtil.init_logger()
    logger = elog()
    logger.info("初始化阶段...")

    logger.info("安装依赖模块...")
    commonUtil.installpackage(args["whlsource"])

    logger.info("初始化完成")
    return "OK"


def train(args):
    from ai.prepare_data import PrepareData
    import shutil
    commonUtil.setRootPath(os.path.split(os.path.realpath(__file__))[0])
    logger = elog()

    # if os.path.exists("gen"):
    #     shutil.rmtree("gen")
    # if os.path.exists("graph"):
    #     os.remove("graph")
    # os.makedirs("gen/data")
    # os.makedirs("gen/models/intent_model")
    # os.makedirs("gen/models/word_slot_model")
    # commonUtil.init_dict(args["dicturl"], "gen/data/dict.txt") #
    # commonUtil.downloadModel(logger, url=args["bertmodel"], zippath="gen/bertmodel.zip", tarpath="gen/models")

    # 下载基础词典

    dp = PrepareData(args)

    dp.intent_train_data()
    #commonUtil.uploadModel(logger, args["classifier_model_name"], "gen/models/intent_model", args["savemodelurl"])

    dp.word_slot_train_data()
    #commonUtil.uploadModel(logger, args["word_slot_model_name"], "gen/models/word_slot_model", args["savemodelurl"])

    return "OK"


def predict(args):
    from rasa_server import RASAServer
    from epointml.utils import DbPoolUtil
    import json
    import shutil
    commonUtil.setRootPath(os.path.split(os.path.realpath(__file__))[0])
    logger = elog()

    # if os.path.exists("gen"):
    #     shutil.rmtree("gen")
    # if os.path.exists("graph"):
    #     os.remove("graph")
    # os.makedirs("gen/data")
    # os.makedirs("gen/models/intent_model")
    # os.makedirs("gen/models/word_slot_model")
    # commonUtil.init_dict(args["dicturl"], "gen/data/dict.txt")
    # commonUtil.downloadModel(logger, url=args["bertmodel"], zippath="gen/bertmodel.zip", tarpath="gen/models")

    # # 下载启动模型
    # commonUtil.downloadModel(logger, url=args["classifier_model_url"], zippath="gen/classifier_model.zip",
    #                          tarpath="gen/models/intent_model")
    # commonUtil.downloadModel(logger, url=args["word_slot_model_url"], zippath="gen/word_slot_model.zip",
    #                          tarpath="gen/models/word_slot_model")

    rasaserver = RASAServer(args, logger)
    con = DbPoolUtil(jdbcurl=args["jdbcurl"])
    sql = """select * from {0}""".format(args["table"])
    data = con.execute_query(sql, dict_mark=True)
    confidence = float(args["confidence"])
    # print(data)
    for d in data:
        predict_data = rasaserver.intent_model.parse(d[args["content"]])
        print(predict_data)
        if len(predict_data["entities"]) > 0 and predict_data["intent"]["confidence"] > confidence:
            con.execute("""update {0} set target_hat=%s, labeltype_hat=%s where {1}=%s""".format(args["table"],
                                                                                                 args["rowguid"]), (
                        json.dumps(predict_data["entities"], ensure_ascii=False), predict_data["intent"]["name"],
                        d[args["rowguid"]]))
        elif len(predict_data["entities"]) > 0:
            con.execute("""update {0} set target_hat=%s where {1}=%s""".format(args["table"], args["rowguid"]),
                        (json.dumps(predict_data["entities"], ensure_ascii=False), d[args["rowguid"]]))
        elif predict_data["intent"]["confidence"] > confidence:
            con.execute("""update {0} set labeltype_hat=%s where {1}=%s""".format(args["table"], args["rowguid"]),
                        (predict_data["intent"]["name"], d[args["rowguid"]]))
    return "OK"


def deploy(args):
    """
    发布阶段
    :return:
    """
    import shutil
    from flask import Flask
    from flask_cors import CORS
    from ai.rasa_server import RASAServer
    commonUtil.setRootPath(os.path.split(os.path.realpath(__file__))[0])
    logger = elog()
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"  # Only needed on OSX
    # if os.path.exists("gen"):
    #     shutil.rmtree("gen")
    # if os.path.exists("graph"):
    #     os.remove("graph")
    # os.makedirs("gen/data")
    # os.makedirs("gen/models/intent_model")
    # os.makedirs("gen/models/word_slot_model")
    # commonUtil.downloadModel(logger, url=args["bertmodel"], zippath="gen/bertmodel.zip", tarpath="gen/models")
    # # 下载启动模型
    # commonUtil.downloadModel(logger, url=args["classifier_model_url"], zippath="gen/classifier_model.zip",
    #                          tarpath="gen/models/intent_model")
    # commonUtil.downloadModel(logger, url=args["word_slot_model_url"], zippath="gen/word_slot_model.zip",
    #                          tarpath="gen/models/word_slot_model")
    rasaserver = RASAServer(args, logger)
    app = Flask(__name__)
    # 跨域设置
    CORS(app)
    # 绑定路由
    app.add_url_rule("/{}/check".format(args["serviceName"]), None, getattr(rasaserver, "api_check"), methods=['GET'])
    app.add_url_rule("/{}/predict".format(args["serviceName"]), None, getattr(rasaserver, "api_predict"),
                     methods=["POST"])

    # 启动服务
    commonUtil.sendRestReadySignal()
    app.run(host='0.0.0.0', port=int(args["port"]), debug=False)
    logger.info("服务已开启")
    # 暂时先用独立的Flask server. 生产环境中把服务注册到WSGI Server中，并挂到Nginx上.
    return "OK"


def main(tp):
    commonUtil.setRootPath(os.path.split(os.path.realpath(__file__))[0])
    init(commonUtil.load_step_param("init"))
    if tp == "1":
        train(commonUtil.load_step_param("train"))

    if tp == "2":
        predict(commonUtil.load_step_param("predict"))

    if tp == "3":
        deploy(commonUtil.load_step_param("deploy"))


if __name__ == "__main__":
    tpe = "1"# input("请选择对应的模式（1：训练模式，2：发布模式）:")
    # while tpe != "1" and tpe != "2":
    #     tpe = input("输入错误请重新输入对应的模式（1：训练模式，2：发布模式）:")
    # print(type(tp))
    main(tpe)
