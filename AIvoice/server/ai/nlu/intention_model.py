# -*- coding: utf-8 -*-
from epointml.utils import elog
import jieba
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
import datetime
import pickle


class NaturalLanguageInterpreter(object):
    def __init__(self, word_slot_model):
        self.logger = elog()
        self.question = []
        self.answer = []
        self.ner = word_slot_model
        self.model = None

    def train(self, data):
        raise NotImplementedError

    def init_model(self):
        raise NotImplementedError

    def parse(self, text):
        raise NotImplementedError

    def word_slot_parse(self, text):
        raise NotImplementedError

    @staticmethod
    def name():
        raise NotImplementedError


class SimpleNluInterpreter(NaturalLanguageInterpreter):
    def __init__(self, word_slot_model=None):
        super().__init__(word_slot_model)

    def train(self, data):
        from gensim.summarization.bm25 import BM25
        if not os.path.exists("gen/models/intent_model/bm25.pkl") or not os.path.exists(
                "gen/models/intent_model/bm25_answer.pkl") or not os.path.exists(
            "gen/models/intent_model/bm25_question.pkl"):
            with open("gen/models/intent_model/bm25.pkl", "wb") as f:
                for d in data:
                    self.question.append(d["content"])
                    self.answer.append(d["labeltype"])
                self.question = [list(jieba.cut(q)) for q in self.question]
                self.model = BM25(self.question)
                pkl_str = pickle.dumps(self.model)
                f.write(pkl_str)
            with open("gen/models/intent_model/bm25_answer.pkl", "wb") as f:
                pkl_str = pickle.dumps(self.answer)
                f.write(pkl_str)
            with open("gen/models/intent_model/bm25_question.pkl", "wb") as f:
                pkl_str = pickle.dumps(self.question)
                f.write(pkl_str)
        else:
            self.init_model()

    def init_model(self):
        with open("gen/models/intent_model/bm25.pkl", 'rb') as f:
            self.model = pickle.loads(f.read())
        with open("gen/models/intent_model/bm25_answer.pkl", 'rb') as f:
            self.answer = pickle.loads(f.read())
        with open("gen/models/intent_model/bm25_question.pkl", 'rb') as f:
            self.question = pickle.loads(f.read())

    def parse(self, text):
        words = list(jieba.cut(text))
        score = self.model.get_scores(words)
        intent = self.answer[score.index(max(score))]
        data = self.question[score.index(max(score))]
        c = self.confidence(set(words) & set(data), set(words) | set(data))
        entities = self.ner.predict(text=text)
        return {
            "text": text,
            "intent": {
                "name": intent,
                "confidence": c
            },
            "entities": entities["entities"]
        }

    def word_slot_parse(self, text):
        entities = self.ner.predict(text=text)
        return {
            "text": text,
            "intent": None,
            "entities": entities["entities"]
        }

    def confidence(self, set1, set2):
        p1 = 0
        p2 = 0
        for s in set1:
            if s in self.model.idf:
                p1 += self.model.idf[s]
            else:
                p1 += 1
        for s in set2:
            if s in self.model.idf:
                p2 += self.model.idf[s]
            else:
                p2 += 1
        return p1 / p2

    @staticmethod
    def name():
        return "BM25"


class BertNluInterpreter(NaturalLanguageInterpreter):
    def __init__(self, word_slot_model=None):
        super().__init__(word_slot_model)
        from nlu.bert_sim.extract_feature import BertVector
        self.model = BertVector()

    def train(self, data):
        if not os.path.exists("gen/models/intent_model/bert_vec.npy") or not os.path.exists(
                "gen/models/intent_model/bert_answer.pkl"):
            for d in data:
                print(d)
                self.question.append(self.model.encode([d["content"]])[0])
                self.answer.append(d["labeltype"])
            np.save("gen/models/intent_model/bert_vec.npy", self.question)
            with open("gen/models/intent_model/bert_answer.pkl", "wb") as f:
                pkl_str = pickle.dumps(self.answer)
                f.write(pkl_str)
        else:
            self.init_model()

    def init_model(self):
        with open("gen/models/intent_model/bert_answer.pkl", 'rb') as f:
            self.answer = pickle.loads(f.read())
        self.question = np.load("gen/models/intent_model/bert_vec.npy")
        a = datetime.datetime.now()
        self.model.encode(["text"])
        print(datetime.datetime.now() - a)

    def parse(self, text):
        words = self.model.encode([text])[0]
        score = cosine_similarity(self.question, [np.array(words)]).tolist()
        intent = self.answer[score.index(max(score))]
        entities = self.ner.predict(text=text)
        return {
            "text": text,
            "intent": {
                "name": intent,
                "confidence": max(score)[0]
            },
            "entities": entities["entities"]
        }

    def word_slot_parse(self, text):
        entities = self.ner.predict(text=text)
        return {
            "text": text,
            "intent": None,
            "entities": entities["entities"]
        }

    @staticmethod
    def name():
        return "Bert"


if __name__ == "__main__":
    loggers = elog()
    sni = BertNluInterpreter()
    out = sni.parse("吴亦凡帅")
    print(out)
