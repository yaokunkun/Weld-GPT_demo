import datetime

task = 'intent_recognize'
config = {
    'param_control':{
        'label_list': ['up', 'down', 'control'],
        'save_dir': f"../models/{task}/{datetime.datetime.now().strftime('%y-%m-%d-%H-%M-%S')}",
        'model_dir': "/dev_data_2/zkyao/code/Weld-GPT_demo/models/bert-base-chinese",
        'device': 'cuda',
        'do_train': True,
        'train_dataset_path': "param_control/train.json",
        'do_validate': True,
        'validate_dataset_path': "param_control/validate.json",
        'do_test': True,
        'test_dataset_path': "param_control/test.json",
        'metrics': "accuracy",
        # hypeparameters
        'seed': 42,
        'learning_rate': 2e-5,
        'per_device_train_batch_size': 8,
        'per_device_eval_batch_size': 8,
        'num_epoch': 5,
        'weight_decay':0.01
    },
    'intent_recognize':{
        'label_list': ['QUERY', 'CONTROL', 'RAG'],
        'save_dir': f"../models/{task}/{datetime.datetime.now().strftime('%y-%m-%d-%H-%M-%S')}",
        'model_dir': "/dev_data_2/zkyao/code/Weld-GPT_demo/models/bert-base-chinese",
        'device': 'cuda',
        'do_train': True,
        'train_dataset_path': "intent_recognize/train.json",
        'do_validate': True,
        'validate_dataset_path': "intent_recognize/validate.json",
        'do_test': True,
        'test_dataset_path': "intent_recognize/test.json",
        'metrics': "accuracy",
        # hypeparameters
        'seed': 42,
        'learning_rate': 2e-5,
        'per_device_train_batch_size': 8,
        'per_device_eval_batch_size': 8,
        'num_epoch': 5,
        'weight_decay':0.01
    }
}