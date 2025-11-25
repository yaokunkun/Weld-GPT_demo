import datetime

task_config = {
    'param_control':{
        'label_list': ['up', 'down', 'control'],
        'save_dir': f"./models/param_control/{datetime.datetime.now().strftime('%y-%m-%d-%H-%M-%S')}",
        'model_dir': "/dev_data_2/zkyao/code/Weld-GPT_demo/models/bert-base-chinese",
        'do_train': True,
        'train_dataset_path': "param_control/train.json",
        'do_validate': True,
        'validate_dataset_path': "param_control/validate.json",
        'do_test': True,
        'test_dataset_path': "param_control/test.json",
    },
    'intent_recognize':{
        'label_list': ['QUERY', 'CONTROL', 'RAG'],
        'save_dir': f"./models/intent_recognize/{datetime.datetime.now().strftime('%y-%m-%d-%H-%M-%S')}",
        'model_dir': "/dev_data_2/zkyao/code/Weld-GPT_demo/models/bert-base-chinese",
        'do_train': True,
        'train_dataset_path': "intent_recognize/train.json",
        'do_validate': True,
        'validate_dataset_path': "intent_recognize/validate.json",
        'do_test': True,
        'test_dataset_path': "intent_recognize/test.json",
    },
    'param_control_en':{
        'label_list': ['up', 'down', 'control'],
        'save_dir': f"./models/param_control_en/{datetime.datetime.now().strftime('%y-%m-%d-%H-%M-%S')}",
        'model_dir': "/dev_data/zkyao/pretrain_model/bert-base-uncased",
        'do_train': True,
        'train_dataset_path': "param_control_en/train.json",
        'do_validate': True,
        'validate_dataset_path': "param_control_en/validate.json",
        'do_test': True,
        'test_dataset_path': "param_control_en/test.json",
    },
    'intent_recognize_en':{
        'label_list': ['QUERY', 'CONTROL', 'RAG'],
        'save_dir': f"./models/intent_recognize_en/{datetime.datetime.now().strftime('%y-%m-%d-%H-%M-%S')}",
        'model_dir': "/dev_data/zkyao/pretrain_model/bert-base-uncased",
        'do_train': True,
        'train_dataset_path': "sentence_classify/intent_recognize_en/train.jsonl",
        'do_validate': True,
        'validate_dataset_path': "sentence_classify/intent_recognize_en/validate.json",
        'do_test': True,
        'test_dataset_path': "sentence_classify/intent_recognize_en/test.json",
    },
}
train_config = {
    'task': 'intent_recognize_en',
    'device': 'cuda',
    'visible_gpus': '1',
    'seed': 42,
    'learning_rate': 2e-5,
    'per_device_train_batch_size': 8,
    'per_device_eval_batch_size': 8,
    'num_epoch': 5,
    'weight_decay':0.01,
    'early_stopping_patience': True, # 是否启用早停
}
test_config = {
    'task': 'intent_recognize_en',
    'device': 'cuda',
    'visible_gpus': '2',
    'checkpoint_dir': "/dev_data/zkyao/code/Weld-GPT_demo/models/intent_recognize_en/25-08-29-06-06-34/checkpoint-10640",
    'per_device_eval_batch_size': 8,
}