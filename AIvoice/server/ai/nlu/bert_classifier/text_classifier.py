# -*- coding=utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections
import os
import tensorflow as tf
import numpy as np

from nlu.bert_classifier.bert import modeling
from nlu.bert_classifier.bert import optimization
from nlu.bert_classifier.bert import tokenization

from nlu.bert_classifier.moonPie import DataProcessor, InputExample, PaddingInputExample, InputFeatures
from tensorflow.contrib import predictor


class MultiLabelClassificationProcessor(DataProcessor):
    def __init__(self):
        self.language = "zh"

    def get_examples(self, data_dir):
        with open(os.path.join(data_dir, "token_in.txt"), encoding='utf-8') as token_in_f:
            with open(os.path.join(data_dir, "label_out.txt"), encoding='utf-8') as label_out_f:
                token_in_list = [seq.replace("\n", '') for seq in token_in_f.readlines()]
                label_list = [seq.replace("\n", '') for seq in label_out_f.readlines()]
                assert len(token_in_list) == len(label_list)
                examples = list(zip(token_in_list, label_list))
                return examples

    def get_train_examples(self, data_dir):
        return self.create_example(self.get_examples(os.path.join(data_dir, "train")), "train")

    def get_dev_examples(self, data_dir):
        return self.create_example(self.get_examples(os.path.join(data_dir, "valid")), "valid")

    def get_test_examples(self, data_dir):
        with open(os.path.join(data_dir, os.path.join("test", "token_in.txt")), encoding='utf-8') as token_in_f:
            token_in_list = [seq.replace("\n", '') for seq in token_in_f.readlines()]
            examples = token_in_list
            return self.create_example(examples, "test")

    def get_labels(self):
        label_path = "gen/models/classification_data/label.txt"
        if not os.path.exists(label_path):
            dirs = os.listdir("gen/models/classification_model")
            latest = str(sorted(dirs)[-1])
            model_path = "gen/models/classification_model/{0}".format(latest)
            label_path = os.path.join(model_path, "label.txt")

        with open(label_path, "r", encoding="utf-8") as f:
            labels = eval(f.read())
        return labels

    def create_example(self, lines, set_type):
        """Creates examples for the training and dev sets."""
        examples = []
        for (i, line) in enumerate(lines):
            guid = "%s-%s" % (set_type, i)
            if set_type == "test":
                text_str = line
                predicate_label_str = ''
            else:
                text_str = line[0]
                predicate_label_str = line[1]
            examples.append(
                InputExample(guid=guid, text_a=text_str, text_b=None, label=predicate_label_str))
        return examples


def convert_single_example(ex_index, example, label_list, max_seq_length, tokenizer):
    """Converts a single `InputExample` into a single `InputFeatures`."""

    if isinstance(example, PaddingInputExample):
        return InputFeatures(
            input_ids=[0] * max_seq_length,
            input_mask=[0] * max_seq_length,
            segment_ids=[0] * max_seq_length,
            label_ids=[0] * len(label_list),
            is_real_example=False)

    label_map = {}
    for (i, label) in enumerate(label_list):
        label_map[label] = i

    tokens_a = example.text_a.split(" ")
    tokens_b = None
    if example.text_b:
        tokens_b = tokenizer.tokenize(example.text_b)

    if tokens_b:
        # Modifies `tokens_a` and `tokens_b` in place so that the total
        # length is less than the specified length.
        # Account for [CLS], [SEP], [SEP] with "- 3"
        _truncate_seq_pair(tokens_a, tokens_b, max_seq_length - 3)
    else:
        # Account for [CLS] and [SEP] with "- 2"
        if len(tokens_a) > max_seq_length - 2:
            tokens_a = tokens_a[0:(max_seq_length - 2)]

    # The convention in BERT is:
    # (a) For sequence pairs:
    #  tokens:   [CLS] is this jack ##son ##ville ? [SEP] no it is not . [SEP]
    #  type_ids: 0     0  0    0    0     0       0 0     1  1  1  1   1 1
    # (b) For single sequences:
    #  tokens:   [CLS] the dog is hairy . [SEP]
    #  type_ids: 0     0   0   0  0     0 0
    #
    # Where "type_ids" are used to indicate whether this is the first
    # sequence or the second sequence. The embedding vectors for `type=0` and
    # `type=1` were learned during pre-training and are added to the wordpiece
    # embedding vector (and position vector). This is not *strictly* necessary
    # since the [SEP] token unambiguously separates the sequences, but it makes
    # it easier for the model to learn the concept of sequences.
    #
    # For classification tasks, the first vector (corresponding to [CLS]) is
    # used as the "sentence vector". Note that this only makes sense because
    # the entire model is fine-tuned.
    tokens = []
    segment_ids = []
    tokens.append("[CLS]")
    segment_ids.append(0)
    for token in tokens_a:
        tokens.append(token)
        segment_ids.append(0)
    tokens.append("[SEP]")
    segment_ids.append(0)

    if tokens_b:
        for token in tokens_b:
            tokens.append(token)
            segment_ids.append(1)
        tokens.append("[SEP]")
        segment_ids.append(1)

    input_ids = tokenizer.convert_tokens_to_ids(tokens)

    # The mask has 1 for real tokens and 0 for padding tokens. Only real
    # tokens are attended to.
    input_mask = [1] * len(input_ids)

    label_list = example.label.split(" ")
    label_ids = _predicate_label_to_id(label_list, label_map)

    # Zero-pad up to the sequence length.
    while len(input_ids) < max_seq_length:
        input_ids.append(0)
        input_mask.append(0)
        segment_ids.append(0)

    assert len(input_ids) == max_seq_length
    assert len(input_mask) == max_seq_length
    assert len(segment_ids) == max_seq_length

    feature = InputFeatures(
        input_ids=input_ids,
        input_mask=input_mask,
        segment_ids=segment_ids,
        label_ids=label_ids,
        is_real_example=True)
    return feature


def _predicate_label_to_id(predicate_label, predicate_label_map):
    predicate_label_map_length = len(predicate_label_map)
    predicate_label_ids = [0] * predicate_label_map_length
    for label in predicate_label:
        predicate_label_ids[predicate_label_map[label]] = 1
    return predicate_label_ids


def file_based_convert_examples_to_features(
        examples, label_list, max_seq_length, tokenizer, output_file):
    """Convert a set of `InputExample`s to a TFRecord file."""

    writer = tf.python_io.TFRecordWriter(output_file)

    for (ex_index, example) in enumerate(examples):
        if ex_index % 10000 == 0:
            tf.logging.info("Writing example %d of %d" % (ex_index, len(examples)))

        feature = convert_single_example(ex_index, example, label_list,
                                         max_seq_length, tokenizer)

        def create_int_feature(values):
            f = tf.train.Feature(int64_list=tf.train.Int64List(value=list(values)))
            return f

        features = collections.OrderedDict()
        features["input_ids"] = create_int_feature(feature.input_ids)
        features["input_mask"] = create_int_feature(feature.input_mask)
        features["segment_ids"] = create_int_feature(feature.segment_ids)
        features["label_ids"] = create_int_feature(feature.label_ids)
        features["is_real_example"] = create_int_feature(
            [int(feature.is_real_example)])

        tf_example = tf.train.Example(features=tf.train.Features(feature=features))
        writer.write(tf_example.SerializeToString())
    writer.close()


def file_based_input_fn_builder(input_file, seq_length, label_length,
                                is_training, drop_remainder):
    """Creates an `input_fn` closure to be passed to TPUEstimator."""

    name_to_features = {
        "input_ids": tf.FixedLenFeature([seq_length], tf.int64),
        "input_mask": tf.FixedLenFeature([seq_length], tf.int64),
        "segment_ids": tf.FixedLenFeature([seq_length], tf.int64),
        "label_ids": tf.FixedLenFeature([label_length], tf.int64),
        "is_real_example": tf.FixedLenFeature([], tf.int64),
    }

    def _decode_record(record, name_to_features):
        """Decodes a record to a TensorFlow example."""
        example = tf.parse_single_example(record, name_to_features)

        # tf.Example only supports tf.int64, but the TPU only supports tf.int32.
        # So cast all int64 to int32.
        for name in list(example.keys()):
            t = example[name]
            if t.dtype == tf.int64:
                t = tf.to_int32(t)
            example[name] = t

        return example

    def input_fn(params):
        """The actual input function."""
        batch_size = params["batch_size"]

        # For training, we want a lot of parallel reading and shuffling.
        # For eval, we want no shuffling and parallel reading doesn't matter.
        d = tf.data.TFRecordDataset(input_file)
        if is_training:
            d = d.repeat()
            d = d.shuffle(buffer_size=100)

        d = d.apply(
            tf.contrib.data.map_and_batch(
                lambda record: _decode_record(record, name_to_features),
                batch_size=batch_size,
                drop_remainder=drop_remainder))
        return d
    return input_fn


def _truncate_seq_pair(tokens_a, tokens_b, max_length):
    """Truncates a sequence pair in place to the maximum length."""

    # This is a simple heuristic which will always truncate the longer sequence
    # one token at a time. This makes more sense than truncating an equal percent
    # of tokens from each, since if one sequence is very short then each token
    # that's truncated likely contains more information than a longer sequence.
    while True:
        total_length = len(tokens_a) + len(tokens_b)
        if total_length <= max_length:
            break
        if len(tokens_a) > len(tokens_b):
            tokens_a.pop()
        else:
            tokens_b.pop()


def create_model(bert_config, is_training, input_ids, input_mask, segment_ids,
                 labels, num_labels):
    """Creates a classification model."""
    model = modeling.BertModel(
        config=bert_config,
        is_training=is_training,
        input_ids=input_ids,
        input_mask=input_mask,
        token_type_ids=segment_ids,
        use_one_hot_embeddings=True)

    # In the demo, we are doing a simple classification task on the entire
    # segment.
    #
    # If you want to use the token-level output, use model.get_sequence_output()
    # instead.
    output_layer = model.get_pooled_output()

    hidden_size = output_layer.shape[-1].value

    output_weights = tf.get_variable(
        "output_weights", [num_labels, hidden_size],
        initializer=tf.truncated_normal_initializer(stddev=0.02))

    output_bias = tf.get_variable(
        "output_bias", [num_labels], initializer=tf.zeros_initializer())

    with tf.variable_scope("loss"):
        if is_training:
            # I.e., 0.1 dropout
            output_layer = tf.nn.dropout(output_layer, keep_prob=0.9)

        logits_wx = tf.matmul(output_layer, output_weights, transpose_b=True)
        logits = tf.nn.bias_add(logits_wx, output_bias)
        probabilities = tf.sigmoid(logits)
        label_ids = tf.cast(labels, tf.float32)
        per_example_loss = tf.reduce_sum(
            tf.nn.sigmoid_cross_entropy_with_logits(logits=logits, labels=label_ids), axis=-1)
        # tf.logging.info(per_example_loss)  # check code
        loss = tf.reduce_mean(per_example_loss)

        return loss, per_example_loss, logits, probabilities


def model_fn_builder(bert_config, num_labels, init_checkpoint, learning_rate,
                     num_train_steps, num_warmup_steps,
                     args):

    def model_fn(features, labels, mode, params):  # pylint: disable=unused-argument
        """The `model_fn` for TPUEstimator."""

        # tf.logging.info("*** Features ***")
        # for name in sorted(features.keys()):
        #     tf.logging.info("  name = %s, shape = %s" % (name, features[name].shape))
        # print("features ", features)
        # features = features.__next__()
        # print("features ", features)

        input_ids = features["input_ids"]
        input_mask = features["input_mask"]
        segment_ids = features["segment_ids"]
        label_ids = features["label_ids"]

        # if "is_real_example" in features:
        #     is_real_example = tf.cast(features["is_real_example"], dtype=tf.float32)
        # else:
        #     is_real_example = tf.ones(tf.shape(label_ids), dtype=tf.float32)

        is_training = (mode == tf.estimator.ModeKeys.TRAIN)

        (total_loss, per_example_loss, logits, probabilities) = create_model(
            bert_config, is_training, input_ids, input_mask, segment_ids, label_ids,
            num_labels)

        tvars = tf.trainable_variables()
        initialized_variable_names = {}

        if init_checkpoint:
            (assignment_map, initialized_variable_names
             ) = modeling.get_assignment_map_from_checkpoint(tvars, init_checkpoint)

            tf.train.init_from_checkpoint(init_checkpoint, assignment_map)

        tf.logging.info("**** Trainable Variables ****")
        for var in tvars:
            init_string = ""
            if var.name in initialized_variable_names:
                init_string = ", *INIT_FROM_CKPT*"
            tf.logging.info("  name = %s, shape = %s%s", var.name, var.shape,
                            init_string)

        if mode == tf.estimator.ModeKeys.TRAIN:

            train_op = optimization.create_optimizer(
                total_loss, learning_rate, num_train_steps, num_warmup_steps)

            hook_dict = {'loss': total_loss, 'global_steps': tf.train.get_or_create_global_step()}
            logging_hook = tf.estimator.LoggingTensorHook(
                hook_dict, every_n_iter=args["save_summary_steps"])

            output_spec = tf.estimator.EstimatorSpec(
                mode=mode,
                loss=total_loss,
                train_op=train_op,
                training_hooks=[logging_hook]
            )
        elif mode == tf.estimator.ModeKeys.EVAL:

            def metric_fn(per_example_loss, label_ids, probabilities):
                predict_ids = tf.cast(probabilities > 0.5, tf.int32)
                label_ids = tf.cast(label_ids, tf.int32)
                elements_equal = tf.cast(tf.equal(predict_ids, label_ids), tf.int32)
                # change [batch_size, class_numbers] to [1, batch_size]
                row_predict_ids = tf.reduce_sum(elements_equal, -1)
                row_label_ids = tf.reduce_sum(tf.ones_like(label_ids), -1)
                accuracy = tf.metrics.accuracy(
                    labels=row_label_ids, predictions=row_predict_ids)
                loss = tf.metrics.mean(values=per_example_loss)
                return {
                    "eval_accuracy": accuracy,
                    "eval_loss": loss,
                }

            eval_metrics = metric_fn(per_example_loss, label_ids, probabilities)

            output_spec = tf.estimator.EstimatorSpec(
                mode=mode,
                loss=total_loss,
                eval_metric_ops=eval_metrics
            )
        else:
            output_spec = tf.estimator.EstimatorSpec(
                mode=mode,
                predictions={"probabilities": probabilities}
            )
        return output_spec

    return model_fn


def train(train_cls_args):
    tf.logging.set_verbosity(tf.logging.INFO)

    processors = {
        "label_classifier": MultiLabelClassificationProcessor,
    }
    tokenization.validate_case_matches_checkpoint(train_cls_args["do_lower_case"], train_cls_args["init_checkpoint"])

    if not train_cls_args["do_train"] and not train_cls_args["do_eval"] and not train_cls_args["do_predict"]:
        raise ValueError(
            "At least one of `do_train`, `do_eval` or `do_predict' must be True.")

    bert_config = modeling.BertConfig.from_json_file(train_cls_args["bert_config_file"])

    if train_cls_args["max_seq_length"] > bert_config.max_position_embeddings:
        raise ValueError(
            "Cannot use sequence length %d because the BERT model "
            "was only trained up to sequence length %d" %
            (train_cls_args["max_seq_length"], bert_config.max_position_embeddings))

    tf.io.gfile.MakeDirs(train_cls_args["output_dir"])

    task_name = train_cls_args["task_name"].lower()

    if task_name not in processors:
        raise ValueError("Task not found: %s" % task_name)

    processor = processors[task_name]()

    label_list = processor.get_labels()
    label_length = len(label_list)

    tokenizer = tokenization.FullTokenizer(
        vocab_file=train_cls_args["vocab_file"], do_lower_case=train_cls_args["do_lower_case"])

    gpu_options = tf.GPUOptions(allow_growth=True)
    session_config = tf.ConfigProto(
        log_device_placement=False,
        inter_op_parallelism_threads=0,
        intra_op_parallelism_threads=0,
        allow_soft_placement=True,
        gpu_options=gpu_options)

    run_config = tf.estimator.RunConfig(
        model_dir=train_cls_args["output_dir"],
        save_checkpoints_steps=train_cls_args["save_checkpoints_steps"],
        session_config=session_config
    )

    train_examples = None
    num_train_steps = None
    num_warmup_steps = None

    if train_cls_args["do_train"]:
        train_examples = processor.get_train_examples(train_cls_args["data_dir"])
        num_train_steps = int(
            len(train_examples) / train_cls_args["train_batch_size"] * train_cls_args["num_train_epochs"])
        num_warmup_steps = int(num_train_steps * train_cls_args["warmup_proportion"])

    model_fn = model_fn_builder(
        bert_config=bert_config,
        num_labels=len(label_list),
        init_checkpoint=train_cls_args["init_checkpoint"],
        learning_rate=train_cls_args["learning_rate"],
        num_train_steps=num_train_steps,
        num_warmup_steps=num_warmup_steps,
        args=train_cls_args)

    params = {
        "batch_size": train_cls_args["train_batch_size"]
    }
    estimator = tf.estimator.Estimator(
        model_fn=model_fn,
        config=run_config,
        params=params
    )

    if train_cls_args["do_train"]:
        train_file = os.path.join(train_cls_args["output_dir"], "train.tf_record")
        file_based_convert_examples_to_features(
            train_examples, label_list, train_cls_args["max_seq_length"], tokenizer, train_file)
        tf.logging.info("***** Running training *****")
        tf.logging.info("  Num examples = %d", len(train_examples))
        tf.logging.info("  Batch size = %d", train_cls_args["train_batch_size"])
        tf.logging.info("  Num steps = %d", num_train_steps)
        train_input_fn = file_based_input_fn_builder(
            input_file=train_file,
            seq_length=train_cls_args["max_seq_length"],
            label_length=label_length,
            is_training=True,
            drop_remainder=True)

        eval_examples = processor.get_dev_examples(train_cls_args["data_dir"])
        num_actual_eval_examples = len(eval_examples)

        eval_file = os.path.join(train_cls_args["output_dir"], "eval.tf_record")
        file_based_convert_examples_to_features(
            eval_examples, label_list, train_cls_args["max_seq_length"], tokenizer, eval_file)

        tf.logging.info("***** Running evaluation *****")
        tf.logging.info("  Num examples = %d (%d actual, %d padding)",
                        len(eval_examples), num_actual_eval_examples,
                        len(eval_examples) - num_actual_eval_examples)
        tf.logging.info("  Batch size = %d", train_cls_args["eval_batch_size"])

        eval_input_fn = file_based_input_fn_builder(
            input_file=eval_file,
            seq_length=train_cls_args["max_seq_length"],
            label_length=label_length,
            is_training=False,
            drop_remainder=False
        )

        early_stopping_hook = tf.estimator.experimental.stop_if_no_decrease_hook(
            estimator=estimator,
            metric_name='loss',
            max_steps_without_decrease=num_train_steps,  # 1000
            eval_dir=None,
            min_steps=0,
            run_every_secs=None,
            run_every_steps=train_cls_args["save_checkpoints_steps"])

        estimator.train(input_fn=train_input_fn, max_steps=num_train_steps)
        train_spec = tf.estimator.TrainSpec(input_fn=train_input_fn, max_steps=num_train_steps,
                                            hooks=[early_stopping_hook])
        eval_spec = tf.estimator.EvalSpec(input_fn=eval_input_fn)
        tf.estimator.train_and_evaluate(estimator, train_spec=train_spec, eval_spec=eval_spec)

        # 导出模型代码
        def serving_input_receiver_fn():
            receiver_tensors = {
                "input_ids": tf.placeholder(dtype=tf.int64, shape=[None, train_cls_args["max_seq_length"]],
                                            name="input_ids"),
                "input_mask": tf.placeholder(dtype=tf.int64, shape=[None, train_cls_args["max_seq_length"]],
                                             name="input_mask"),
                "segment_ids": tf.placeholder(dtype=tf.int64, shape=[None, train_cls_args["max_seq_length"]],
                                              name="segment_ids"),
                "label_ids": tf.placeholder(dtype=tf.int64, shape=[None, label_length],
                                            name="label_ids"),
                # "is_real_example": tf.placeholder(dtype=tf.int64, shape=[1, label_length],
                #                                   name="is_real_example")
            }
            return tf.estimator.export.ServingInputReceiver(receiver_tensors, receiver_tensors)

        # export estimator model
        if not os.path.exists("gen/models/classification_model"):
            os.makedirs("gen/models/classification_model")
        estimator.export_saved_model("gen/models/classification_model", serving_input_receiver_fn)


class PredicateAnalyser:
    def __init__(self, args):
        self.args = args

        self.processors = {
            "label_classifier": MultiLabelClassificationProcessor,
        }

        if not args["do_train"] and not args["do_eval"] and not args["do_predict"]:
            raise ValueError(
                "At least one of `do_train`, `do_eval` or `do_predict' must be True.")

        self.bert_config = modeling.BertConfig.from_json_file(args["bert_config_file"])

        if args["max_seq_length"] > self.bert_config.max_position_embeddings:
            raise ValueError(
                "Cannot use sequence length %d because the BERT model "
                "was only trained up to sequence length %d" %
                (args["max_seq_length"], self.bert_config.max_position_embeddings))

        task_name = args["task_name"].lower()

        if task_name not in self.processors:
            raise ValueError("Task not found: %s" % task_name)
        self.processor = self.processors[task_name]()

        self.label_list = self.processor.get_labels()
        self.label_length = len(self.label_list)

        self.tokenizer = tokenization.FullTokenizer(
            vocab_file=args["vocab_file"], do_lower_case=args["do_lower_case"])

        gpu_options = tf.GPUOptions(allow_growth=True)
        session_config = tf.ConfigProto(
            log_device_placement=False,
            inter_op_parallelism_threads=0,
            intra_op_parallelism_threads=0,
            allow_soft_placement=True,
            gpu_options=gpu_options)

        run_config = tf.estimator.RunConfig(
            model_dir=args["output_dir"],
            save_checkpoints_steps=args["save_checkpoints_steps"],
            keep_checkpoint_max=1,  # 算子中只保存一个模型，调试的时候自己多保存几个测试
            session_config=session_config
        )

        self.train_examples = None
        self.num_train_steps = None
        num_warmup_steps = None

        if self.args["do_train"]:
            self.train_examples = self.processor.get_train_examples(self.args["data_dir"])
            self.num_train_steps = int(
                len(self.train_examples) / self.args["train_batch_size"] * self.args["num_train_epochs"])
            num_warmup_steps = int(self.num_train_steps * self.args["warmup_proportion"])

        model_fn = model_fn_builder(
            bert_config=self.bert_config,
            num_labels=len(self.label_list),
            init_checkpoint=args["init_checkpoint"],
            learning_rate=args["learning_rate"],
            num_train_steps=self.num_train_steps,
            num_warmup_steps=num_warmup_steps,
            args=args)

        params = {
            "batch_size": args["train_batch_size"]
        }
        self.estimator = tf.estimator.Estimator(
            model_fn=model_fn,
            config=run_config,
            params=params
        )

        # make some folders.
        if not os.path.exists(self.args["output_dir"]):
            os.makedirs(self.args["output_dir"])

        # fast predictor
        dirs = os.listdir("gen/models/classification_model")
        latest = str(sorted(dirs)[-1])
        self.predictor = predictor.from_saved_model("gen/models/classification_model/{0}".format(latest))

    def fast_convert(self, tokens):
        example = InputExample(guid="0", text_a=tokens, text_b=None, label="")
        feature = convert_single_example(0, example, self.label_list, self.args["max_seq_length"], self.tokenizer)

        def create_int_feature(values):
            # f = tf.train.Feature(int64_list=tf.train.Int64List(value=list(values)))
            # f = tf.train.Feature(tf.train.Int)
            f = np.array([values])
            return f

        features = collections.OrderedDict()

        features["input_ids"] = create_int_feature(feature.input_ids)
        features["input_mask"] = create_int_feature(feature.input_mask)
        features["segment_ids"] = create_int_feature(feature.segment_ids)
        features["label_ids"] = create_int_feature(feature.label_ids)

        return features

    def fast_predict(self, sentence):
        """
        快速预测
        :param sentence:
        :return:
        """
        tokens = " ".join(self.tokenizer.tokenize(sentence))
        features = self.fast_convert(tokens)

        prediction = self.predictor(features)
        probabilities = prediction["probabilities"][0]
        predicate_predict = []
        for idx, class_probability in enumerate(probabilities):
            if class_probability > 0:  # 这个概率阈值需要根据业务场景调整
                predicate_predict.append((self.label_list[idx], class_probability))
        if len(predicate_predict) == 0:
            index_num = np.argmax(probabilities)
            predicate_predict.append((self.label_list[index_num], probabilities[index_num]))
        return sentence, tokens, predicate_predict


if __name__ == "__main__":
    train_cls_args = {
        "data_dir": "gen/classification_data",
        "bert_config_file": "gen/chinese_bert/bert_config.json",
        "task_name": "label_classifier",
        "vocab_file": "gen/chinese_bert/vocab.txt",
        "output_dir": "gen/output/predicate_infer_out",
        "init_checkpoint": "gen/chinese_bert/bert_model.ckpt",
        "max_seq_length": 128,
        "do_train": False,
        "do_eval": False,
        "do_predict": True,
        "train_batch_size": 32,
        "eval_batch_size": 8,
        "predict_batch_size": 1,
        "learning_rate": 2e-5,
        "num_train_epochs": 20.0,
        "warmup_proportion": 0.1,
        "save_checkpoints_steps": 500,
        "iterations_per_loop": 500,
        "do_lower_case": True,
        "save_summary_steps": 500
    }
    predicator = PredicateAnalyser(train_cls_args)
    sent = '2015年06月02日02时至3时之间，姚永方（男，320525197102096535，电话13962593376）位于吴江区震泽镇八都贯桥村(12)庵前3号的房内被盗200元现金，损失价值约200元。'
    ret = predicator.fast_predict(sent)
    print("predict result: ", ret)