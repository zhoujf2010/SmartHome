import tensorflow as tf
from util.PropertiesUtil import prop
from tensorflow.contrib.layers import *
from util.Elog import elog
from sklearn.model_selection import train_test_split


class DNNModel(object):
    def __init__(self):
        params = prop.get_config_dict("config/params.properties")
        self.epoch = int(params["epoch"])
        self.batch = int(params["batch"])
        self.learning_rate = float(params["learningrate"])
        self.keep_prob_per = float(params["keepprob"])
        self.scala = float(params["scala"])
        self.kernels = [int(x) for x in params["kernels"].split(',')]
        self.in_dis, self.out_dis = [int(x) for x in params["inout"].split(',')]
        self.model_path = "model/model.ckpt"

        # 变量
        self.x = None
        self.y = None
        self.keep_prob = None
        # 预测结果
        self.logits = None
        # 优化器
        self.optimize = None
        # 准确率评估
        self.accuracy = None
        # 初始化
        self.init = None
        # 模型存储
        self.saver = None

        self.init_tf()

    def weight_variable(self, shape, name='weights'):
        """
        构建权重
        :param shape: 形状
        :param name: 名称
        :return:
        """
        initial = tf.truncated_normal(shape, dtype=tf.float32, stddev=0.1)
        var = tf.Variable(initial, name=name)
        # 把L2正则化加入集合losses里面
        tf.add_to_collection("l2losses", l2_regularizer(self.scala)(var))
        return var

    @staticmethod
    def bias_variable(shape, name='bias'):
        """
        构建偏置
        :param shape: 形状
        :param name: 名称
        :return:
        """
        initial = tf.constant(0.0, dtype=tf.float32, shape=shape)
        return tf.Variable(initial, name=name)

    @staticmethod
    def fc(inputs, w, b):
        """
        构建神经元公式
        :param inputs: 输入矩阵
        :param w: 权重矩阵
        :param b: 偏置矩阵
        :return:
        """
        return tf.matmul(inputs, w) + b

    def init_tf(self):
        """
        初始化tf图所有变量
        :return:
        """
        self.x = tf.placeholder(tf.float32, shape=[None, self.in_dis], name='input_x')
        self.y = tf.placeholder(tf.float32, shape=[None, self.out_dis], name='output_y')
        self.keep_prob = tf.placeholder(tf.float32)

        # 全连接网络
        with tf.name_scope("dnn"):
            # 第一层输入
            in_dimensions = self.in_dis
            in_data = self.x

            for i in range(len(self.kernels)):
                weight = self.weight_variable([in_dimensions, self.kernels[i]])
                bias = self.bias_variable([self.kernels[i]])
                output = tf.nn.relu(self.fc(in_data, weight, bias))
                in_data = tf.nn.dropout(output, self.keep_prob)
                in_dimensions = self.kernels[i]
                tf.summary.histogram('weight' + str(i), weight)
                tf.summary.histogram('bias' + str(i), bias)

            # 最后一层使用softmax
            f_weight = self.weight_variable([in_dimensions, self.out_dis])
            f_bias = self.bias_variable([self.out_dis])
            f_output = tf.nn.relu(self.fc(in_data, f_weight, f_bias))
            self.logits = tf.nn.softmax(f_output, name='softmax')
            tf.summary.histogram('f_weight', f_weight)
            tf.summary.histogram('f_bias', f_bias)

        # 损失函数与优化器
        with tf.name_scope("loss"):
            base_loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits_v2(logits=self.logits, labels=self.y))
            reg_loss = tf.add_n(tf.get_collection("l2losses"))
            loss = tf.add(base_loss, reg_loss, name="loss")
            self.optimize = tf.train.AdamOptimizer(learning_rate=self.learning_rate).minimize(loss)

        # 准确率
        with tf.name_scope("accuracy"):
            prediction_labels = tf.argmax(self.logits, axis=1, name="output")
            correct_prediction = tf.equal(prediction_labels, tf.argmax(self.y, axis=1))
            self.accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

        # 初始化
        with tf.name_scope("init"):
            self.init = tf.global_variables_initializer()

        self.saver = tf.train.Saver()

    def train(self, features, labels):
        """
        训练模型
        :param features: 特征
        :param labels: 标签
        :return:
        """
        summary_op = tf.summary.merge_all()
        t_features = self.__get_new_features(features)
        small_features, small_labels = self.__get_small(t_features, labels)
        elog.info("训练预测模型")
        with tf.Session() as sess:
            sess.run(self.init)
            writer = tf.summary.FileWriter("graph", sess.graph)
            for i in range(self.epoch):
                x_train, x_test, y_train, y_test = train_test_split(t_features, labels, test_size=0.2, random_state=0,
                                                                    shuffle=True)
                x_test += small_features
                y_test += small_labels
                # 转独热编码
                labels_train = [[0, 1] if label else [1, 0] for label in y_train]
                labels_test = [[0, 1] if label else [1, 0] for label in y_test]
                for j in range(1, len(x_train) // self.batch + 2):
                    print('epoch : ', i + 1, ' batch : ', j)
                    start = self.batch * (j - 1)
                    end = start + self.batch
                    sess.run(self.optimize, feed_dict={self.x: x_train[start:end], self.y: labels_train[start:end],
                                                       self.keep_prob: self.keep_prob_per})
                train_acc = self.accuracy.eval(
                    feed_dict={self.x: x_train, self.y: labels_train, self.keep_prob: self.keep_prob_per})
                tf.summary.scalar('train_acc', train_acc)
                test_acc = self.accuracy.eval(
                    feed_dict={self.x: x_test, self.y: labels_test, self.keep_prob: self.keep_prob_per})
                tf.summary.scalar('test_acc', test_acc)
                summary_str = sess.run(summary_op)
                writer.add_summary(summary_str, i)
                elog.info(str(i + 1) + "： 训练集准确率:" + str(train_acc) + "；测试集准确率:" + str(test_acc))

            writer.close()
            self.saver.save(sess, self.model_path)
            elog.info("模型训练完毕，存储完毕")

    def load_model(self):
        """
        加载模型
        :return:
        """
        elog.info("载入模型")
        sess = tf.Session()
        self.saver.restore(sess, self.model_path)
        # saver = tf.train.import_meta_graph("model/model.ckpt.meta")
        # saver.restore(sess, tf.train.latest_checkpoint('model/'))
        elog.info("载入模型完毕")
        return sess

    def predict(self, sess, features):
        """
        预测
        :param sess: 会话
        :param features: 特征
        :return:
        """
        elog.info("进行预测")
        t_features = self.__get_new_features(features)
        output = sess.run(self.logits, feed_dict={self.x: t_features, self.keep_prob: self.keep_prob_per})
        elog.info("预测完成")
        return output

    def re_train(self, sess, features, labels):
        """
        增量学习
        :param sess: 会话
        :param features: 特征
        :param labels: 标签
        :return:
        """
        elog.info("进行增量学习")
        t_features = self.__get_new_features(features)
        t_labels = [[0, 1] if label else [1, 0] for label in labels]
        sess.run(self.optimize, feed_dict={self.x: t_features, self.y: t_labels, self.keep_prob: self.keep_prob_per})
        self.saver.save(sess, self.model_path)
        elog.info("增量学习完成")
        return "success"

    # ----------------------业务方法-----------------------
    @staticmethod
    def __get_new_features(features):
        """
        获取新维度特征值
        :param features: 原始特征
        :return:
        """
        temp_features = []
        for feature in features:
            # 开具票面平均金额
            average_amount = feature[2] / feature[1] if feature[1] > 0 and feature[2] > 0 else 0
            # 发票限额比例
            limit = average_amount / feature[0] if average_amount > 0 and feature[0] > 0 else 0
            # 交易在外省比例
            provincial = feature[5] / feature[1] if feature[1] > 0 and feature[5] > 0 else 0
            temp_features.append([average_amount, limit, provincial] + feature[1:])
        return temp_features

    @staticmethod
    def __get_small(features, labels):
        """
        过采样，获取不均衡样本中较少的类
        :return:
        """
        small_features = []
        small_labels = []
        for i in range(len(labels)):
            if labels[i]:
                small_features.append(features[i])
                small_labels.append(labels[i])
        return small_features, small_labels


dnn_model = DNNModel()
