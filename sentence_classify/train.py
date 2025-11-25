import os
import numpy as np
from transformers import AutoModelForSequenceClassification, BertTokenizer, Trainer, TrainingArguments, EarlyStoppingCallback
from transformers import DataCollatorWithPadding
from config import task_config, train_config
task_config = task_config[train_config['task']]
from datasets import load_dataset
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

if train_config.get('visible_gpus'):
    os.environ["CUDA_VISIBLE_DEVICES"] = train_config['visible_gpus']
label_list = task_config['label_list']
label_to_id = {label: i for i, label in enumerate(label_list)}
output_dir = task_config['save_dir']
#os.makedirs(output_dir, exist_ok=True)
logging_dir = os.path.join(output_dir, 'logs')
os.makedirs(logging_dir, exist_ok=True)

    
def tokenize_function(examples):
    """Tokenizes the BATCHED input text and labels.

    Args:
        examples: each example: {'input': str, 'label': str}

    Returns:
        each example: each example: {'input': str, 'label': int, 'input_ids': List[int], 'attention_mask': List[int], 'token_type_ids': List[int]}
    """
    tokenized = tokenizer(examples["input"], padding="max_length", truncation=True)
    tokenized["label"] = [label_to_id[label] for label in examples["label"]]
    return tokenized

def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    
    metrics = {
        "accuracy": accuracy_score(labels, predictions),
        "f1_macro": f1_score(labels, predictions, average="macro"),
        "precision_macro": precision_score(labels, predictions, average="macro"),
        "recall_macro": recall_score(labels, predictions, average="macro")
    }
    
    return metrics

if __name__ == '__main__':
    # 1. 加载模型和tokenizer
    tokenizer = BertTokenizer.from_pretrained(task_config['model_dir'])
    model = AutoModelForSequenceClassification.from_pretrained(task_config['model_dir'], num_labels=len(label_list))

    # 2. 加载数据
    train_dataset, validate_dataset, test_dataset = None, None, None
    if task_config['do_train']:
        train_dataset = load_dataset('json', data_files=task_config['train_dataset_path'],split='train' ) #['train']
        train_dataset = train_dataset.map(tokenize_function, batched=True, load_from_cache_file=True).shuffle(seed=train_config['seed'])
    if task_config['do_validate']:
        validate_dataset = load_dataset('json', data_files=task_config['validate_dataset_path'])['train']
        validate_dataset = validate_dataset.map(tokenize_function, batched=True, load_from_cache_file=True)
    if task_config['do_test']:
        test_dataset = load_dataset('json', data_files=task_config['test_dataset_path'])['train']
        test_dataset = test_dataset.map(tokenize_function, batched=True, load_from_cache_file=True)
    ## 定义 data_collator
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    # 3. 加载Trainer
    args = TrainingArguments(
        output_dir=output_dir,
        logging_dir=logging_dir,
        overwrite_output_dir=True,
        learning_rate=train_config['learning_rate'],
        per_device_train_batch_size=train_config['per_device_train_batch_size'],
        per_device_eval_batch_size=train_config['per_device_eval_batch_size'],
        num_train_epochs=train_config['num_epoch'],
        weight_decay=train_config['weight_decay'],
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",  # 使用F1分数作为最佳模型选择标准
        greater_is_better=True,  # F1分数越高越好
        logging_strategy="steps",
        logging_steps=1,
        save_total_limit=3,  # 只保留最新的3个检查点
    )
        
    ## 设置回调函数
    callbacks = []
    if train_config.get('early_stopping_patience'):
        callbacks.append(EarlyStoppingCallback(
            early_stopping_patience=train_config['early_stopping_patience']
        ))

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        eval_dataset=validate_dataset,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
        callbacks=callbacks,
    )

    # 4. 训练和测试
    if task_config['do_train']:
        print('========================== train ==========================')
        resume_from_checkpoint = None
        # 支持断点续训
        if os.path.exists(output_dir) and any(f.startswith("checkpoint") for f in os.listdir(output_dir)):
            resume_from_checkpoint = True
        trainer.train(resume_from_checkpoint=resume_from_checkpoint)
        trainer.save_model()  # 保存最终模型

    if task_config['do_test']:
        print('========================== test ==========================')
        results = trainer.evaluate(eval_dataset=test_dataset)
        print(results)