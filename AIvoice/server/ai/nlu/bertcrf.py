# -*- coding: utf-8 -*-
"""
@author: Adrian
Date: March 7, 2019
"""
import os
import pickle

import tensorflow as tf
import codecs
import numpy as np

from bert_base.bert import tokenization, modeling
# from bert_base.train.train_helper import get_args_parser
from bert_base.train.bert_lstm_ner import train
from bert_base.train.models import create_model, InputFeatures


# args = get_args_parser()

# class train_args():
#     def __init__(self,
#                  bert_path,
#                  root_path,
#                  data_dir="NERdata",
#                  bert_config_file="bert_config.json",
#                  output_dir="output",
#                  init_checkpoint="bert_model.ckpt",
#                  vocab_file="vocab.txt",
#                  max_seq_length=128,
#                  do_train=True,
#                  do_eval=True,
#                  do_predict=True,
#                  batch_size=64,
#                  learning_rate=1e-5,
#                  num_train_epochs=10,
#                  dropout_rate=0.5,
#                  clip=0.5,
#                  warmup_proportion=0.1,
#                  lstm_size=128,
#                  num_layers=1,
#                  cell='lstm',
#                  save_checkpoints_steps=500,
#                  save_summary_steps=500,
#                  filter_adam_var=False,
#                  do_lower_case=True,
#                  clean=True,
#                  device_map='0',
#                  labels=None,
#                  verbose=False,
#                  ner='ner',
#                  version='0.1.0'):
#         self.bert_path = bert_path
#         self.root_path = root_path
#         self.data_dir = data_dir
#         self.bert_config_file = bert_config_file
#         self.output_dir = output_dir
#         self.init_checkpoint = init_checkpoint
#         self.vocab_file = vocab_file
#         self.max_seq_length = max_seq_length
#         self.do_train = do_train
#         self.do_eval = do_eval
#         self.do_predict = do_predict
#         self.batch_size = batch_size
#         self.learning_rate = learning_rate
#         self.num_train_epochs = num_train_epochs
#         self.dropout_rate = dropout_rate
#         self.clip = clip
#         self.warmup_proportion = warmup_proportion
#         self.lstm_size = lstm_size
#         self.num_layers = num_layers
#         self.cell = cell
#         self.save_checkpoints_steps = save_checkpoints_steps
#         self.save_summary_steps = save_summary_steps
#         self.filter_adam_var = filter_adam_var
#         self.do_lower_case = do_lower_case
#         self.clean = clean
#         self.device_map = device_map
#         self.label_list = labels
#         self.verbose = verbose
#         self.ner = ner
#         self.version = version


def train_ner(bert_path,
              root_path,
              data_dir="NERdata",
              bert_config_file="bert_config.json",
              output_dir="output",
              init_checkpoint="bert_model.ckpt",
              vocab_file="vocab.txt",
              max_seq_length=128,
              do_train=True,
              do_eval=True,
              do_predict=True,
              batch_size=64,
              learning_rate=1e-5,
              num_train_epochs=10,
              dropout_rate=0.5,
              clip=0.5,
              warmup_proportion=0.1,
              lstm_size=128,
              num_layers=1,
              cell='lstm',
              save_checkpoints_steps=500,
              save_summary_steps=500,
              filter_adam_var=False,
              do_lower_case=True,
              clean=True,
              device_map='0',
              labels=None,
              verbose=False,
              ner='ner',
              version='0.1.0'):
    """NER模型训练参数
    Parameters
    ----------
    bert_path:
    root_path:
    data_dir:
    bert_config_file:
    output_dir:
    init_checkpoint:
    vocab_file:
    max_seq_length:
    do_train:
    do_eval:
    do_predict:
    batch_size:
    learning_rate:
    num_train_epochs:
    dropout_rate:
    clip:
    warmup_proportion:
    lstm_size:
    num_layers:
    cell:
    save_checkpoints_steps:
    save_summary_steps:
    filter_adam_var:
    do_lower_case:
    clean:
    device_map:
    labels: str， default None
        自定义实体类别，支持文件名或者传参方式传入, 如果是None, 默认做人名，地名，机构名识别。
        传入文件路径名称， 或者传入类别参数，通过","区分。"O,B-TIM,I-TIM,B-PER,I-PER"
    verbose:
    ner:
    version:
    :return:
    """
    args = {
        "bert_path": bert_path,
        "root_path": root_path,
        "data_dir": data_dir,
        "bert_config_file": bert_config_file,
        "output_dir": output_dir,
        "init_checkpoint": init_checkpoint,
        "vocab_file": vocab_file,
        "max_seq_length": max_seq_length,
        "do_train": do_train,
        "do_eval": do_eval,
        "do_predict": do_predict,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "num_train_epochs": num_train_epochs,
        "dropout_rate": dropout_rate,
        "clip": clip,
        "warmup_proportion": warmup_proportion,
        "lstm_size": lstm_size,
        "num_layers": num_layers,
        "cell": cell,
        "save_checkpoints_steps": save_checkpoints_steps,
        "save_summary_steps": save_summary_steps,
        "filter_adam_var": filter_adam_var,
        "do_lower_case": do_lower_case,
        "clean": clean,
        "device_map": device_map,
        "labels": labels,
        "verbose": verbose,
        "ner": ner,
        "version": version
    }

    os.environ['CUDA_VISIBLE_DEVICES'] = args["device_map"]
    # print(args)
    train(args=args)


class ner_runner():
    def __init__(self, model_dir, bert_dir, max_seq_length, do_lower_case=True):
        self.model_dir = model_dir
        self.bert_dir = bert_dir
        self.max_seq_length = max_seq_length
        self.do_lower_case = do_lower_case
        self.is_training = False
        self.use_one_hot_embedding = False
        self.batch_size = 1
        self.gpu_config = tf.ConfigProto()
        self.gpu_config.gpu_options.allow_growth = True
        self.sess = tf.Session(config=self.gpu_config)
        self.model = None
        # graph
        self.input_ids_p, self.input_mask_p, self.label_ids_p, self.segment_ids_p = None, None, None, None

        print('checkpoint path:{}'.format(os.path.join(self.model_dir, "checkpoint")))
        if not os.path.exists(os.path.join(self.model_dir, "checkpoint")):
            raise Exception("failed to get checkpoint. going to return ")

        # 加载label->id的词典
        with codecs.open(os.path.join(self.model_dir, 'label2id.pkl'), 'rb') as rf:
            self.label2id = pickle.load(rf)
            self.id2label = {value: key for key, value in self.label2id.items()}

        with codecs.open(os.path.join(self.model_dir, 'label_list.pkl'), 'rb') as rf:
            self.label_list = pickle.load(rf)
        num_labels = len(self.label_list) + 1

        # 读取模型中的实体标签
        label_helper = self.label_list - {"X", "O", "[SEP]", "[CLS]"}
        self.labeltag = set()
        for i in label_helper:
            tag = i.split("-")[1]
            if tag not in self.labeltag:
                self.labeltag.add(tag)

        self.graph = tf.get_default_graph()
        with self.graph.as_default():
            print("going to restore checkpoint")
            # sess.run(tf.global_variables_initializer())
            self.input_ids_p = tf.placeholder(tf.int32, [self.batch_size, self.max_seq_length], name="input_ids")
            self.input_mask_p = tf.placeholder(tf.int32, [self.batch_size, self.max_seq_length], name="input_mask")

            bert_config = modeling.BertConfig.from_json_file(os.path.join(self.bert_dir, 'bert_config.json'))
            (self.total_loss, self.logits, self.trans, self.pred_ids) = create_model(
                bert_config=bert_config, is_training=False, input_ids=self.input_ids_p, input_mask=self.input_mask_p,
                segment_ids=None,
                labels=None, num_labels=num_labels, use_one_hot_embeddings=False, dropout_rate=1.0)

            self.saver = tf.train.Saver()
            self.saver.restore(self.sess, tf.train.latest_checkpoint(self.model_dir))

        self.tokenizer = tokenization.FullTokenizer(
            vocab_file=os.path.join(self.bert_dir, 'vocab.txt'), do_lower_case=self.do_lower_case)

    def convert(self, line):
        feature = self.convert_single_example(0, line, self.label_list, self.max_seq_length, self.tokenizer, 'p')
        input_ids = np.reshape([feature.input_ids], (self.batch_size, self.max_seq_length))
        input_mask = np.reshape([feature.input_mask], (self.batch_size, self.max_seq_length))
        segment_ids = np.reshape([feature.segment_ids], (self.batch_size, self.max_seq_length))
        label_ids = np.reshape([feature.label_ids], (self.batch_size, self.max_seq_length))
        return input_ids, input_mask, segment_ids, label_ids

    def predict_online(self, sentence):
        """
        do online prediction. each time make prediction for one instance.
        you can change to a batch if you want.

        :param line: a list. element is: [dummy_label,text_a,text_b]
        :return:
        """
        with self.graph.as_default():
            # print(self.id2label)

            # print('input the test sentence:')
            sentence = str(sentence)
            # start = datetime.now()
            # if len(sentence) < 2:
            #     print(sentence)
            text = sentence

            sentence = self.tokenizer.tokenize(sentence)
            # print('your input is:{}'.format(sentence))
            input_ids, input_mask, segment_ids, label_ids = self.convert(sentence)

            feed_dict = {self.input_ids_p: input_ids,
                         self.input_mask_p: input_mask}
            # run session get current feed_dict result
            pred_ids_result = self.sess.run([self.pred_ids], feed_dict)
            pred_label_result = self.convert_id_to_label(pred_ids_result, self.id2label)
            # print("pred_label_result: {}".format(pred_label_result))

            result = self.strage_combined_link_org_loc(sentence, pred_label_result[0])
            result["text"] = text
            return result
            # print('time used: {} sec'.format((datetime.now() - start).total_seconds()))

    def convert_id_to_label(self, pred_ids_result, idx2label):
        """
        将id形式的结果转化为真实序列结果
        :param pred_ids_result:
        :param idx2label:
        :return:
        """
        result = []
        for row in range(self.batch_size):
            curr_seq = []
            for ids in pred_ids_result[row][0]:
                if ids == 0:
                    break
                curr_label = idx2label[ids]
                if curr_label in ['[CLS]', '[SEP]']:
                    continue
                curr_seq.append(curr_label)
            result.append(curr_seq)
        return result

    def strage_combined_link_org_loc(self, tokens, tags):
        """
        组合策略
        :param pred_label_result:
        :param types:
        :return:
        """

        def print_output(data, type):
            line = []
            line.append(type)
            for i in data:
                line.append(i.word)
            print(', '.join(line))

        evalresult = Result(labels=list(self.labeltag))
        if len(tokens) > len(tags):
            tokens = tokens[:len(tags)]
        # container = eval.get_result(tokens, tags)
        # for i in container:
        #     print_output(container[i], i)
        json_result = evalresult.get_result(tokens, tags)
        return json_result

    def convert_single_example(self, ex_index, example, label_list, max_seq_length, tokenizer, mode):
        """
        将一个样本进行分析，然后将字转化为id, 标签转化为id,然后结构化到InputFeatures对象中
        :param ex_index: index
        :param example: 一个样本
        :param label_list: 标签列表
        :param max_seq_length:
        :param tokenizer:
        :param mode:
        :return:
        """
        label_map = {}
        # 1表示从1开始对label进行index化
        for (i, label) in enumerate(label_list, 1):
            label_map[label] = i
        # 保存label->index 的map
        if not os.path.exists(os.path.join(self.model_dir, 'label2id.pkl')):
            with codecs.open(os.path.join(self.model_dir, 'label2id.pkl'), 'wb') as w:
                pickle.dump(label_map, w)

        tokens = example
        # tokens = tokenizer.tokenize(example.text)
        # 序列截断
        if len(tokens) >= max_seq_length - 1:
            tokens = tokens[0:(max_seq_length - 2)]  # -2 的原因是因为序列需要加一个句首和句尾标志
        ntokens = []
        segment_ids = []
        label_ids = []
        ntokens.append("[CLS]")  # 句子开始设置CLS 标志
        segment_ids.append(0)
        # append("O") or append("[CLS]") not sure!
        label_ids.append(label_map["[CLS]"])  # O OR CLS 没有任何影响，不过我觉得O 会减少标签个数,不过拒收和句尾使用不同的标志来标注，使用LCS 也没毛病
        for i, token in enumerate(tokens):
            ntokens.append(token)
            segment_ids.append(0)
            label_ids.append(0)
        ntokens.append("[SEP]")  # 句尾添加[SEP] 标志
        segment_ids.append(0)
        # append("O") or append("[SEP]") not sure!
        label_ids.append(label_map["[SEP]"])
        input_ids = tokenizer.convert_tokens_to_ids(ntokens)  # 将序列中的字(ntokens)转化为ID形式
        input_mask = [1] * len(input_ids)

        # padding, 使用
        while len(input_ids) < max_seq_length:
            input_ids.append(0)
            input_mask.append(0)
            segment_ids.append(0)
            # we don't concerned about it!
            label_ids.append(0)
            ntokens.append("**NULL**")
            # label_mask.append(0)
        # print(len(input_ids))
        assert len(input_ids) == max_seq_length
        assert len(input_mask) == max_seq_length
        assert len(segment_ids) == max_seq_length
        assert len(label_ids) == max_seq_length
        # assert len(label_mask) == max_seq_length

        # 结构化为一个类
        feature = InputFeatures(
            input_ids=input_ids,
            input_mask=input_mask,
            segment_ids=segment_ids,
            label_ids=label_ids,
            # label_mask = label_mask
        )
        return feature


class Pair(object):
    def __init__(self, word, start, end, type, merge=False):
        self.__word = word
        self.__start = start
        self.__end = end
        self.__merge = merge
        self.__types = type

    @property
    def start(self):
        return self.__start

    @property
    def end(self):
        return self.__end

    @property
    def merge(self):
        return self.__merge

    @property
    def word(self):
        return self.__word

    @property
    def types(self):
        return self.__types

    @word.setter
    def word(self, word):
        self.__word = word

    @start.setter
    def start(self, start):
        self.__start = start

    @end.setter
    def end(self, end):
        self.__end = end

    @merge.setter
    def merge(self, merge):
        self.__merge = merge

    @types.setter
    def types(self, type):
        self.__types = type

    def __str__(self) -> str:
        line = []
        line.append('entity:{}'.format(self.__word))
        line.append('start:{}'.format(self.__start))
        line.append('end:{}'.format(self.__end))
        line.append('merge:{}'.format(self.__merge))
        line.append('types:{}'.format(self.__types))
        return '\t'.join(line)


class Result(object):
    def __init__(self, labels=("LOC", "ORG", "PER")):
        """
        Parameters
        ----------
        config:
        labels: list of str
            list of labels, should not have others.
        """
        # self.config = config
        # self.person = []
        # self.loc = []
        # self.org = []
        self.others = []
        self.container = {}
        self.labels = labels
        for i in self.labels:
            self.container[i] = []

    def get_result(self, tokens, tags, config=None):
        # 先获取标注结果
        json_result = self.result_to_json(tokens, tags)
        # print("item stuff: ", item)
        # return self.person, self.loc, self.org
        # return self.container
        return json_result

    def result_to_json(self, string, tags):
        """
        将模型标注序列和输入序列结合 转化为结果
        :param string: 输入序列
        :param tags: 标注结果
        :return:
        """
        item = {"entities": []}
        entity_name = ""
        entity_start = 0
        idx = 0
        last_tag = ''

        for char, tag in zip(string, tags):
            if tag[0] == "S":
                # self.append(char, idx, idx+1, tag[2:])
                item["entities"].append({"value": char, "start": idx, "end": idx + 1, "entity": tag[2:]})
            elif tag[0] == "B":
                if entity_name != '':
                    # self.append(entity_name, entity_start, idx, last_tag[2:])
                    item["entities"].append({"value": entity_name, "start": entity_start, "end": idx, "entity": last_tag[2:]})
                    entity_name = ""
                entity_name += char
                entity_start = idx
            elif tag[0] == "I":
                entity_name += char
            elif tag[0] == "O":
                if entity_name != '':
                    # self.append(entity_name, entity_start, idx, last_tag[2:])
                    item["entities"].append({"value": entity_name, "start": entity_start, "end": idx, "entity": last_tag[2:]})
                    entity_name = ""
            else:
                entity_name = ""
                entity_start = idx
            idx += 1
            last_tag = tag
        if entity_name != '':
            # self.append(entity_name, entity_start, idx, last_tag[2:])
            item["entities"].append({"value": entity_name, "start": entity_start, "end": idx, "entity": last_tag[2:]})
        return item

    # def append(self, word, start, end, tag):
    #     for i in self.labels:
    #         if i == tag:
    #             print(word, start, end, i)
    #             self.container[i].append(Pair(word, start, end, i))
    #
    #         else:
    #             self.others.append(Pair(word, start, end, tag))


if __name__ == "__main__":
    # 训练
    # train_ner(bert_path="gen/data/chinese_bert", root_path='/Users/adrian/Documents/workspace/bert_bilstm_crf_ner',
    #           data_dir='gen/data/train', init_checkpoint='gen/data/chinese_bert/bert_model.ckpt',
    #           output_dir='gen/model',
    #           max_seq_length=128,
    #           num_train_epochs=20,
    #           bert_config_file='gen/data/chinese_bert/bert_config.json',
    #           vocab_file='gen/data/chinese_bert/vocab.txt',
    #           labels=None)

    # 预测
    runner = ner_runner()
    rst = runner.predict_online(sentence="海钓比赛地点在厦门与金门之间的海域。 ")
    print(rst)
