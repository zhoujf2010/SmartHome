# -*- coding: utf-8 -*-
import os
from epointml.utils import elog
from nlu.bert_classifier.setting import train_cls_args, model_path, data_path

os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'


def run_train(args=None):
    """训练步骤的代码"""
    from nlu.bert_classifier.data_manager import label_classifier_data_prepare
    from nlu.bert_classifier.text_classifier import train as cls_train
    import shutil

    logger = elog()

    logger.info("准备训练数据...")

    label_classifier_data_prepare(args, vocab_file=train_cls_args["vocab_file"])

    logger.info("训练测试数据准备完成...")

    logger.info("开始训练分类模型...")

    cls_train(train_cls_args)

    # 模型上传
    dirs = os.listdir("gen/models/classification_model")
    latest = str(sorted(dirs)[-1])
    model_path = "gen/models/classification_model/{0}".format(latest)
    # 将label.txt copy至model_path
    label_path = os.path.join(data_path, "label.txt")
    shutil.copy(label_path, model_path)
    # commonUtil.uploadModel(logger, args["savemodelname"], model_path, args["savemodelurl"])


def get_predict_item(predicate_analyser, item):
    text, tokens, predicate = predicate_analyser.fast_predict(sentence=item[1])
    # 取概率最大的类别, 如果要提取多个关系，根据阈值循环调用
    predicate.sort(key=lambda x: x[1], reverse=True)
    update_item = {
        "rowguid": item[0],
        "predict_result": predicate[0][0]
    }
    return update_item
