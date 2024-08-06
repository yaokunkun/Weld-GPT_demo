import os
os.environ["CUDA_VISIBLE_DEVICES"] = "4"

# # 控制台调试
# import os
# os.chdir('intent_and_slot/')

import numpy as np
from transformers import AutoModelForTokenClassification, BertTokenizer, Trainer, TrainingArguments
from config import Config
from dataset import BertDataset
from preprocess_en import Processor, get_features
import evaluate

config = Config()
label_list = config.label_list
output_dir = config.save_dir + '0521'
logging_dir = os.path.join(output_dir, 'logs')
os.makedirs(logging_dir, exist_ok=True)

def eval_metric(pred):
    predictions, labels = pred
    predictions = np.argmax(predictions, axis=-1)

    # 将id转换为原始的字符串类型的标签
    true_predictions = [
        [label_list[p] for p, l in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]

    true_labels = [
        [label_list[l] for p, l in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]

    result = seqeval.compute(predictions=true_predictions, references=true_labels, mode="strict", scheme="IOB2")

    return {
        'precision': result['overall_precision'],
        'recall': result['overall_recall'],
        'f1': result['overall_f1'],
        'accuracy': result['overall_accuracy']
    }


if __name__ == '__main__':
    config = Config()
    # device = config.device
    # 加载模型和tokenizer
    tokenizer = BertTokenizer.from_pretrained(config.bert_dir)
    model = AutoModelForTokenClassification.from_pretrained(config.bert_dir, num_labels=len(label_list))

    # 加载数据
    train_dataset, validate_dataset, test_dataset = None, None, None
    if config.do_train:
        raw_examples = Processor.get_examples(config.train_path, 'train')
        train_features = get_features(raw_examples, tokenizer, config)
        train_dataset = BertDataset(train_features)

        raw_examples = Processor.get_examples(config.validate_path, 'validate')
        validate_features = get_features(raw_examples, tokenizer, config)
        validate_dataset = BertDataset(validate_features)

    # 加载评价指标
    seqeval = evaluate.load("seqeval_metric.py")

    if config.do_test:
        raw_examples = Processor.get_examples(config.test_path, 'test')
        test_features = get_features(raw_examples, tokenizer, config)
        test_dataset = BertDataset(test_features)

    args = TrainingArguments(
        output_dir=output_dir,
        logging_dir=logging_dir,
        overwrite_output_dir=True,
        learning_rate=2e-5,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        num_train_epochs=10,
        weight_decay=0.01,
        evaluation_strategy="epoch",
        logging_strategy="steps",
        logging_steps=1,
    )
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        eval_dataset=validate_dataset,
        compute_metrics=eval_metric,
    )

    if config.do_train:
        print('========================== train ==========================')
        trainer.train()

    if config.do_test:
        trainer.evaluate(eval_dataset=test_dataset)

    # if args.do_predict:
    #     with open('./data/predict.json','r') as fp:
    #         pred_data = eval(fp.read())
    #         for i, p_data in enumerate(pred_data):
    #             text = p_data['text']
    #             print(f'========================== predict example-{i} ==========================')
    #             print('文本：', text)
    #             trainer.predict(text, tokenizer)
    #             print(' ')
