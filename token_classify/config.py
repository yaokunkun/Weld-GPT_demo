import datetime

task_config = {
    'param_extract_en':{
        'label_list': ['up', 'down', 'control'],
        'save_dir': f"../models/param_control_en/{datetime.datetime.now().strftime('%y-%m-%d-%H-%M-%S')}",
        'model_dir': "/dev_data/zkyao/pretrain_model/bert-base-uncased",
        'do_train': True,
        'train_dataset_path': "param_control_en/train.json",
        'do_validate': True,
        'validate_dataset_path': "param_control_en/validate.json",
        'do_test': True,
        'test_dataset_path': "param_control_en/test.json",
    },
}
train_config = {
    'task': 'intent_recognize_en',
    'device': 'cuda',
    'visible_gpus': '0,1',
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
    'visible_gpus': '0,1',
    'checkpoint_dir': "/dev_data/zkyao/code/Weld-GPT_demo/models/intent_recognize_en/25-06-14-03-02-26/checkpoint-300",
    'per_device_eval_batch_size': 8,
}