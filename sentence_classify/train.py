import os
os.environ["CUDA_VISIBLE_DEVICES"] = "4"

import numpy as np
from transformers import AutoModelForSequenceClassification, BertTokenizer, Trainer, TrainingArguments
from transformers import DataCollatorWithPadding
from config import task, config
from datasets import load_dataset

config = config[task]
label_list = config['label_list']
output_dir = config['save_dir']
logging_dir = os.path.join(output_dir, 'logs')
os.makedirs(logging_dir, exist_ok=True)
label_to_id = {label: i for i, label in enumerate(label_list)}

if config['metrics'] == 'accuracy':
    def compute_metrics(eval_pred):
        predictions, labels = eval_pred
        predictions = np.argmax(predictions, axis=1)
        correct_predictions = np.sum(predictions == labels)
        total_samples = len(labels)
        accuracy = correct_predictions / total_samples
        return {"accuracy": accuracy}
else:
    raise ValueError(f"metrics {config['metrics']} not completed!")

def tokenize_function(examples):
    tokenized = tokenizer(examples["input"], padding="max_length", truncation=True)
    tokenized["label"] = [label_to_id[label] for label in examples["label"]]
    return tokenized

if __name__ == '__main__':
    # 加载模型和tokenizer
    tokenizer = BertTokenizer.from_pretrained(config['model_dir'])
    model = AutoModelForSequenceClassification.from_pretrained(config['model_dir'], num_labels=len(label_list))

    # 加载数据
    train_dataset, validate_dataset, test_dataset = None, None, None
    if config['do_train']:
        train_dataset = load_dataset('json', data_files=config['train_dataset_path'])['train']
        train_dataset = train_dataset.map(tokenize_function, batched=True).shuffle(seed=config['seed'])
    if config['do_validate']:
        validate_dataset = load_dataset('json', data_files=config['validate_dataset_path'])['train']
        validate_dataset = validate_dataset.map(tokenize_function, batched=True).shuffle(seed=config['seed'])
    
    # 定义 data_collator
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    if config['do_test']:
        test_dataset = load_dataset('json', data_files=config['test_dataset_path'])['train']
        test_dataset = test_dataset.map(tokenize_function, batched=True).shuffle(seed=config['seed'])

    args = TrainingArguments(
        output_dir=output_dir,
        logging_dir=logging_dir,
        overwrite_output_dir=True,
        learning_rate=config['learning_rate'],
        per_device_train_batch_size=config['per_device_train_batch_size'],
        per_device_eval_batch_size=config['per_device_eval_batch_size'],
        num_train_epochs=config['num_epoch'],
        weight_decay=config['weight_decay'],
        evaluation_strategy="epoch",
        logging_strategy="steps",
        logging_steps=1,
    )
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        eval_dataset=validate_dataset,
        data_collator=data_collator,
        compute_metrics=compute_metrics if compute_metrics else None,
    )

    if config['do_train']:
        print('========================== train ==========================')
        trainer.train()

    if config['do_test']:
        print('========================== test ==========================')
        results = trainer.evaluate(eval_dataset=test_dataset)
        print(results)