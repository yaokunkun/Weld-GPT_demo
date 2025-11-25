import os
import numpy as np
from transformers import AutoModelForTokenClassification, BertTokenizer, Trainer, TrainingArguments, EarlyStoppingCallback
from transformers import DataCollatorWithPadding
from config import task_config, train_config
task_config = task_config[train_config['task']]
from datasets import load_dataset
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

if train_config.get('visible_gpus'):
    os.environ["CUDA_VISIBLE_DEVICES"] = train_config['visible_gpus']

# 自动生成完整的BIO标签列表（O、B-和I-）
entity_types = task_config['label_list']
label_list = ["O"] + [f"B-{etype}" for etype in entity_types] + [f"I-{etype}" for etype in entity_types]
label_to_id = {label: i for i, label in enumerate(label_list)}
id_to_label = {i: label for i, label in enumerate(label_list)}
output_dir = task_config['save_dir']
logging_dir = os.path.join(output_dir, 'logs')
os.makedirs(logging_dir, exist_ok=True)

    
def tokenize_function(examples):
    """Tokenizes the BATCHED input text and aligns NER labels with tokenized words.

    Args:
        examples: each example: {'input': str, 'label': dict[str, str]}
            a example: {
                "input": "我的焊接材料是纯铝，焊接厚度是4，焊接方法是药芯电弧焊。",
                "label": [{"MET": "药芯电弧焊"}, {"MAT": "纯铝"}, {"THI": "4"}]
            }
    Returns:
        each example: {'input': str, 'label': List[int], 'input_ids': List[int], 'attention_mask': List[int], 'token_type_ids': List[int]}
            a example: {
                "input": "我的焊接材料是纯铝，焊接厚度是4，焊接方法是药芯电弧焊。",
                "label": [0, 0, 0, 0, 1, 2, 0, 0, 0, 0, 3, 4, 4, 0, 0, 0, 0, 5, 6, 0, 0],
                "input_ids": [101, 2769, ...],
                "attention_mask": [...],
                "token_type_ids": [...]
            }
    """
    tokenized_inputs = tokenizer(
        examples["input"],
        padding="max_length",
        truncation=True,
        return_offsets_mapping=True  # 需要offsets来定位实体
    )
    labels = []
    for i, (text, entities) in enumerate(zip(examples["input"], examples["label"])):
        # 逐个遍历batch中的每个example
        # 首先每个token的label全部初始化为'O'
        label_ids = [label_to_id["O"]] * len(tokenized_inputs["input_ids"][i])
        
        # 处理input中的每个实体：[{"MET": "药芯电弧焊"}, {"MAT": "纯铝"}, {"THI": "4"}]
        for entity_dict in entities:
            for entity_type, entity_text in entity_dict.items():
                # 在原始文本中查找实体位置
                start_idx = text.find(entity_text)
                if start_idx == -1:
                    continue
                end_idx = start_idx + len(entity_text)
                
                # 找到对应的token位置
                tokens_started = False
                for token_idx, (token_start, token_end) in enumerate(tokenized_inputs["offset_mapping"][i]):
                    # 特殊token（如[CLS], [SEP]）的offset为(0,0)，跳过
                    if token_start == 0 and token_end == 0:
                        continue
                    
                    # 如果start_idx <= token_start <= token_end <= end_idx
                    if token_start >= start_idx and token_end <= end_idx:
                        if not tokens_started:
                            # 实体的第一个token标记为B-
                            label_ids[token_idx] = label_to_id[f"B-{entity_type}"]
                            tokens_started = True
                        else:
                            # 实体的后续token标记为I-
                            label_ids[token_idx] = label_to_id[f"I-{entity_type}"]
                
        labels.append(label_ids)
        
    tokenized_inputs.pop("offset_mapping", None)
    tokenized_inputs["labels"] = labels
    return tokenized_inputs

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
        train_dataset = load_dataset('json', data_files=task_config['train_dataset_path'])['train']
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