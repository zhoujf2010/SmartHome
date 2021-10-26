model_path = "gen/models/classification_model"
data_path = "gen/models/classification_data"

train_cls_args = {
    "data_dir": "gen/models/classification_data",
    "bert_config_file": "gen/models/chinese_bert/bert_config.json",
    "task_name": "label_classifier",
    "vocab_file": "gen/models/chinese_bert/vocab.txt",
    "output_dir": "gen/output/predicate_classification_model",
    "init_checkpoint": "gen/models/chinese_bert/bert_model.ckpt",
    "max_seq_length": 128,
    "do_train": True,
    "do_eval": True,
    "do_predict": False,
    "train_batch_size": 8,
    "eval_batch_size": 32,
    "predict_batch_size": 8,
    "learning_rate": 2e-5,
    "num_train_epochs": 30.0,
    "warmup_proportion": 0.1,
    "save_checkpoints_steps": 500,
    "iterations_per_loop": 500,
    "do_lower_case": True,
    "save_summary_steps": 500
}

deploy_cls_args = {
    "data_dir": "gen/models/classification_data",
    "bert_config_file": "gen/models/chinese_bert/bert_config.json",
    "task_name": "label_classifier",
    "vocab_file": "gen/models/chinese_bert/vocab.txt",
    "output_dir": "gen/output/predicate_classification_model",
    "init_checkpoint": "gen/models/chinese_bert/bert_model.ckpt",
    "max_seq_length": 128,
    "do_train": False,
    "do_eval": False,
    "do_predict": True,
    "train_batch_size": 8,
    "eval_batch_size": 32,
    "predict_batch_size": 8,
    "learning_rate": 2e-5,
    "num_train_epochs": 30.0,
    "warmup_proportion": 0.1,
    "save_checkpoints_steps": 500,
    "iterations_per_loop": 500,
    "do_lower_case": True,
    "save_summary_steps": 500
}
