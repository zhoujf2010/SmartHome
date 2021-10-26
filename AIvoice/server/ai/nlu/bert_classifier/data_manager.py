# -*- coding: utf-8 -*-
"""
数据准备， 为分类模型，序列标注模型准备训练集，开发集，测试集数据。
"""

import os
from nlu.bert_classifier.bert import tokenization
import random


def read_from_local_file(fname="gen/zw.xlsx"):
    import pandas as pd
    import numpy as np
    df = pd.read_excel(fname)

    ftrain = open("gen/train_data2.json", "w", encoding="utf-8")
    fdev = open("gen/dev_data2.json", "w", encoding="utf-8")
    for i in range(len(df)):
        if df["dnote"][i] is not np.NaN:
            line = str({"text": df["question"][i].replace("\n", ""), "spo_list": eval(df["dnote"][i])}) + "\n"
            ftrain.write(line)
            fdev.write(line)
    ftrain.close()
    fdev.close()


def read_from_db(args):
    """
    从数据库中读取标注数据，生成train, dev数据
    :return:
    """
    from epointml.utils import DbPoolUtil

    con = DbPoolUtil(jdbcurl=args["jdbcurl"])
    result = con.execute_query("SELECT MESSAGE feature, INTENTGUID label from rasa_sheet  where 1=1 and calltype='in'")

    data_list = []
    for line in result:
        if len(line) == 2:
            if not line[1]:
                continue
            label_list = line[1].split('**')
            item = {"text": line[0], "label_list": ["p" + label_list[0].replace("-", "")]}
            data_list.append(item)
    random.shuffle(data_list)
    k = int(len(data_list) * 0.8)

    train = data_list[:k]
    dev = data_list[k:]
    with open("gen/models/train_data.json", "w", encoding="utf-8") as f:
        for line in train:
            f.write(str(line) + "\n")
    with open("gen/models/dev_data.json", "w", encoding="utf-8") as f:
        for line in dev:
            f.write(str(line) + "\n")


class ClassifierDataPreparation(object):
    def __init__(self, raw_data_input_dir="gen/models", data_output_dir="classfication_data",
                 vocab_file_path="vocab.txt", do_lower_case=True, competition_mode=False, valid_model=False):
        """
        :param raw_data_input_dir: 输入文件目录，一般是原始数据目录
        :param data_output_dir: 输出文件目录，一般是分类任务数据文件夹
        :param vocab_file_path: 词表路径，一般是预先训练的模型的词表路径
        :param do_lower_case: 默认TRUE
        :param competition_mode: 非比赛模式下，会把验证valid数据作为测试test数据生成
        :param valid_model: 验证模式下，仅仅会生成test测试数据
        """
        # BERT 自带WordPiece分词工具，对于中文都是分成单字
        self.bert_tokenizer = tokenization.FullTokenizer(vocab_file=vocab_file_path, do_lower_case=do_lower_case)
        self.DATA_INPUT_DIR = raw_data_input_dir
        self.DATA_OUTPUT_DIR = os.path.join(self.DATA_INPUT_DIR, data_output_dir)
        self.Competition_Mode = competition_mode
        self.Valid_Model = valid_model
        self.labels = ['']
        print("数据输入路径：", self.DATA_INPUT_DIR)
        print("数据输出路径：", self.DATA_OUTPUT_DIR)
        print("是否是比赛模式（非比赛模式下，会把验证valid数据作为测试test数据生成）：", self.Competition_Mode)
        print("是否是验证模式（验证模式下，仅仅会生成test测试数据）：", self.Valid_Model)

    # 处理原始数据
    def separate_raw_data_and_token_labeling(self):
        if not os.path.exists(self.DATA_OUTPUT_DIR):
            os.makedirs(os.path.join(self.DATA_OUTPUT_DIR, "train"))
            os.makedirs(os.path.join(self.DATA_OUTPUT_DIR, "valid"))
            os.makedirs(os.path.join(self.DATA_OUTPUT_DIR, "test"))

        file_set_type_list = ["train", "valid", "test"]
        if self.Valid_Model:
            file_set_type_list = ["test"]
        for file_set_type in file_set_type_list:
            print("produce data will store in: ", os.path.join(self.DATA_OUTPUT_DIR, file_set_type))
            if file_set_type in ["train", "valid"] or not self.Competition_Mode:
                label_out_f = open(
                    os.path.join(os.path.join(self.DATA_OUTPUT_DIR, file_set_type), "label_out.txt"), "w",
                    encoding='utf-8')
            text_f = open(os.path.join(os.path.join(self.DATA_OUTPUT_DIR, file_set_type), "text.txt"), "w",
                          encoding='utf-8')
            token_in_f = open(os.path.join(os.path.join(self.DATA_OUTPUT_DIR, file_set_type), "token_in.txt"), "w",
                              encoding='utf-8')
            token_in_not_UNK_f = open(
                os.path.join(os.path.join(self.DATA_OUTPUT_DIR, file_set_type), "token_in_not_UNK.txt"), "w",
                encoding='utf-8')

            def label_list_to_label_file(label_list):
                self.labels += label_list  # 将训练数据中的关系标签存入
                label_list_str = " ".join(label_list)
                label_out_f.write(label_list_str + "\n")

            if file_set_type == "train":
                path_to_raw_data_file = "train_data.json"  # 训练数据
            elif file_set_type == "valid":
                path_to_raw_data_file = "dev_data.json"  # 开发数据
            else:
                path_to_raw_data_file = "dev_data.json"  # 测试数据集，和开发共用一个，可自定义

            with open(os.path.join(self.DATA_INPUT_DIR, path_to_raw_data_file), 'r', encoding='utf-8') as f:
                count_numbers = 0
                while True:
                    line = f.readline()
                    if line:
                        count_numbers += 1
                        r = eval(line)
                        if file_set_type in ["train", "valid"]:
                            label_list = r["label_list"]
                        else:
                            label_list = []
                        text = r["text"]
                        text_tokened = self.bert_tokenizer.tokenize(text)
                        text_tokened_not_UNK = self.bert_tokenizer.tokenize_not_UNK(text)

                        if (not self.Competition_Mode) or file_set_type in ["train", "valid"]:
                            label_list_to_label_file(label_list)
                        text_f.write(text + "\n")
                        token_in_f.write(" ".join(text_tokened) + "\n")
                        token_in_not_UNK_f.write(" ".join(text_tokened_not_UNK) + "\n")
                    else:
                        break
            print("all numbers", count_numbers)
            text_f.close()
            token_in_f.close()
            token_in_not_UNK_f.close()

        self.labels = list(set(self.labels))
        with open(self.DATA_OUTPUT_DIR + "/label.txt", "w", encoding="utf-8") as f:
            f.write(str(self.labels))


def label_classifier_data_prepare(args, vocab_file):
    read_from_db(args)
    model_data = ClassifierDataPreparation(
        raw_data_input_dir="gen/models", data_output_dir="classification_data", competition_mode=True,
        valid_model=False, vocab_file_path=vocab_file)
    model_data.separate_raw_data_and_token_labeling()


