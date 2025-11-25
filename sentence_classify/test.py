import os
import numpy as np
from transformers import AutoModelForSequenceClassification, BertTokenizer, Trainer, TrainingArguments
from config import task_config, test_config
task_config = task_config[test_config['task']]
from datasets import load_dataset
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

if test_config.get('visible_gpus'):
    os.environ["CUDA_VISIBLE_DEVICES"] = test_config['visible_gpus']
label_list = task_config['label_list']
label_to_id = {label: i for i, label in enumerate(label_list)}
    
def tokenize_function(examples):
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
    model = AutoModelForSequenceClassification.from_pretrained(test_config['checkpoint_dir'], num_labels=len(label_list))

    # 2. 加载数据
    test_dataset = load_dataset('json', data_files=task_config['test_dataset_path'])['train']
    test_dataset = test_dataset.map(tokenize_function, batched=True,load_from_cache_file=True)

    # 3. 加载Trainer
    args = TrainingArguments(
        per_device_eval_batch_size=test_config['per_device_eval_batch_size'],
    )
    
    trainer = Trainer(
        model=model,
        args=args,
        compute_metrics=compute_metrics,
        
    )

    # 4. 测试
    results = trainer.evaluate(eval_dataset=test_dataset)
    print(results)