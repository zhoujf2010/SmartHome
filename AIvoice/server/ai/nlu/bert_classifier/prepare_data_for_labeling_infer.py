import os


def get_labels():
    # 暂时写死，读某个路径下的配置文件
    with open("gen/classification_data/label.txt", "r", encoding="utf-8") as f:
        labels = eval(f.read())
    return labels


# 对于没有预测出关系的句子，启发式地选择相对概率最大的10个关系作为输出
def replace_empty_infer_predicate_to_three_possible_values(predicate_score_value):
    label_list = get_labels()
    predicate_score_value_list = predicate_score_value.split(" ")
    predicate_score_name_value_list = [(label, value) for label, value in zip(label_list, predicate_score_value_list)]
    predicate_score_name_value_sort_list = sorted(predicate_score_name_value_list, key=lambda x: x[1], reverse=True)
    name_value_three_items = predicate_score_name_value_sort_list[:10]
    three_predicate_list = [name for name, value in name_value_three_items]
    return three_predicate_list


def prepare_data_for_subject_object_labeling_infer(predicate_classifiction_input_file_dir="gen/classification_data/test",
                                                   predicate_classifiction_infer_file_dir=None,
                                                   out_file="gen/sequence_labeling_data/test"):
    """
    Converting the predicted results of the multi-label classification model
    into the input format required by the sequential label model
    :param predicate_classifiction_input_file_dir: Path of Input file of classification model
    :param predicate_classifiction_infer_file_dir: Path of Predictive Output of Classification Model
    :param out_file: Path of Input file of sequential labeling model
    :return: Input file of sequential labeling model
    """
    if not os.path.exists(out_file):
        os.makedirs(out_file)

    with open(os.path.join(predicate_classifiction_input_file_dir, "text.txt"), "r", encoding='utf-8') as f:
        text_file = f.readlines()

    with open(os.path.join(predicate_classifiction_input_file_dir, "token_in.txt"), "r", encoding='utf-8') as f:
        token_in_file = f.readlines()

    with open(os.path.join(predicate_classifiction_input_file_dir, "token_in_not_UNK.txt"), "r", encoding='utf-8') as f:
        token_in_not_unk_file = f.readlines()

    with open(os.path.join(predicate_classifiction_infer_file_dir, "predicate_predict.txt"), "r",
              encoding='utf-8') as f:
        predicate_predict_file = f.readlines()

    with open(os.path.join(predicate_classifiction_infer_file_dir, "predicate_score_value.txt"), "r",
              encoding='utf-8') as f:
        predicate_score_value_file = f.readlines()

    output_text_file_write = open(os.path.join(out_file, "text_and_one_predicate.txt"), "w", encoding='utf-8')
    output_token_in_file_write = open(os.path.join(out_file, "token_in_and_one_predicate.txt"), "w", encoding='utf-8')
    output_token_in_not_unk_file_write = open(os.path.join(out_file, "token_in_not_UNK_and_one_predicate.txt"), "w",
                                              encoding='utf-8')
    count_line = 0
    count_empty_line = 0
    count_temporary_one_predicate_line = 0
    for text, token_in, token_in_not_UNK, predicate_predict, predicate_score_value in zip(text_file, token_in_file,
                                                                                          token_in_not_unk_file,
                                                                                          predicate_predict_file,
                                                                                          predicate_score_value_file):
        count_line += 1
        predicate_list = predicate_predict.replace("\n", "").split(" ")
        if predicate_predict == "\n":
            count_empty_line += 1
            predicate_list = replace_empty_infer_predicate_to_three_possible_values(predicate_score_value)
        for predicate in predicate_list:
            count_temporary_one_predicate_line += 1
            output_text_file_write.write(text.replace("\n", "") + "\t" + predicate + "\n")
            output_token_in_file_write.write(token_in.replace("\n", "") + "\t" + predicate + "\n")
            output_token_in_not_unk_file_write.write(token_in_not_UNK.replace("\n", "") + "\t" + predicate + "\n")
    print("empty_line: {}, line: {}, empty percentage: {:.2f}%".format(count_empty_line, count_line,
                                                                       (count_empty_line / count_line) * 100))
    print("temporary_one_predicate_line: ", count_temporary_one_predicate_line)
    print("输入文件行数：", count_line)
    print("转换成一个text 对应一个 predicate 之后行数变为：", count_temporary_one_predicate_line)

    output_text_file_write.close()
    output_token_in_file_write.close()
    output_token_in_not_unk_file_write.close()


if __name__ == "__main__":
    predicate_classifiction_input_file_dir = "gen/classification_data/test"
    predicate_classifiction_infer_file_dir = None  # None表示使用最新模型输出
    out_file = "gen/sequence_labeling_data/test"
    prepare_data_for_subject_object_labeling_infer(predicate_classifiction_input_file_dir,
                                                   predicate_classifiction_infer_file_dir, out_file)
