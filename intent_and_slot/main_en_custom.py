import os
os.environ["CUDA_VISIBLE_DEVICES"] = "3"

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.optim import Adam
from transformers import BertTokenizer, Trainer, TrainingArguments
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from intent_and_slot.config import Config
from intent_and_slot.model import BertForIntentAndSlot
from dataset import BertDataset
from preprocess_en import Processor, get_features



class CustomTrainer(Trainer):
    def __init__(self, model, args, config, train_dataset=None, eval_dataset=None, tokenizer=None, data_collator=None, **kwargs):
        super().__init__(model=model, args=args, train_dataset=train_dataset, eval_dataset=eval_dataset, tokenizer=tokenizer, data_collator=data_collator, **kwargs)
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = Adam(self.model.parameters(), lr=args.learning_rate)
        self.config = config
        # self.device = config.device

    def compute_loss(self, model, inputs, **kwargs):
        # input_ids = inputs['input_ids'].to(self.device)
        # attention_mask = inputs['attention_mask'].to(self.device)
        # seq_label_ids = inputs['seq_label_ids'].to(self.device)
        # token_label_ids = inputs['token_label_ids'].to(self.device)
        input_ids = inputs['input_ids']
        out_of_range_ids = [idx for idx in input_ids.flatten().tolist() if idx >= tokenizer.vocab_size]
        if out_of_range_ids:
            print(f"超出范围的输入 ID: {out_of_range_ids}")
            raise ValueError("输入 ID 包含超出词汇表范围的值")
        attention_mask = inputs['attention_mask']
        seq_label_ids = inputs['seq_label_ids']
        token_label_ids = inputs['token_label_ids']

        seq_output, token_output = model(input_ids, attention_mask)

        active_loss = attention_mask.view(-1) == 1
        active_logits = token_output.view(-1, token_output.shape[2])[active_loss]
        active_labels = token_label_ids.view(-1)[active_loss]

        seq_loss = self.criterion(seq_output, seq_label_ids)
        token_loss = self.criterion(active_logits, active_labels)
        loss = seq_loss + token_loss

        return loss

    # def evaluate(self, eval_dataset=None, **kwargs):
    #     eval_dataloader = DataLoader(eval_dataset, batch_size=self.args.eval_batch_size)
    #     self.model.eval()
    #     eval_loss = 0
    #     num_batches = 0
    #     seq_preds = []
    #     seq_trues = []
    #     token_preds = []
    #     token_trues = []
    #
    #     with torch.no_grad():
    #         for step, batch in enumerate(eval_dataloader):
    #             for key in batch.keys():
    #                 batch[key] = batch[key].to(self.device)
    #
    #             input_ids = batch['input_ids']
    #             attention_mask = batch['attention_mask']
    #             seq_label_ids = batch['seq_label_ids']
    #             token_label_ids = batch['token_label_ids']
    #
    #             seq_output, token_output = self.model(input_ids, attention_mask)
    #
    #             loss = self.compute_loss(self.model, batch)
    #             eval_loss += loss.item()
    #             num_batches += 1
    #
    #             # Process sequence output
    #             seq_output = seq_output.detach().cpu().numpy()
    #             seq_output = np.argmax(seq_output, -1)
    #             seq_label_ids = seq_label_ids.detach().cpu().numpy().reshape(-1)
    #             seq_preds.extend(seq_output)
    #             seq_trues.extend(seq_label_ids)
    #
    #             # Process token output
    #             token_output = token_output.detach().cpu().numpy()
    #             token_output = np.argmax(token_output, -1)
    #             token_label_ids = token_label_ids.detach().cpu().numpy()
    #             active_len = torch.sum(attention_mask, -1).view(-1)
    #             for length, t_output, t_label in zip(active_len, token_output, token_label_ids):
    #                 t_output = t_output[1:length-1]
    #                 t_label = t_label[1:length-1]
    #                 t_output = [self.config.id2ner_label[i] for i in t_output]
    #                 t_label = [self.config.id2ner_label[i] for i in t_label]
    #                 token_preds.append(t_output)
    #                 token_trues.append(t_label)
    #
    #     avg_eval_loss = eval_loss / num_batches
    #     seq_acc, seq_precision, seq_recall, seq_f1 = self.get_metrices(seq_trues, seq_preds, 'seq')
    #     token_acc, token_precision, token_recall, token_f1 = self.get_metrices(token_trues, token_preds, 'token')
    #
    #     print(f'[eval] loss:{round(avg_eval_loss, 6)} seq_acc:{round(seq_acc, 6)} token_acc:{round(token_acc, 6)}')
    #
    #     return {
    #         'eval_loss': avg_eval_loss,
    #         'seq_acc': seq_acc,
    #         'token_acc': token_acc,
    #         'seq_precision': seq_precision,
    #         'seq_recall': seq_recall,
    #         'seq_f1': seq_f1,
    #         'token_precision': token_precision,
    #         'token_recall': token_recall,
    #         'token_f1': token_f1
    #     }
    #
    # def get_metrices(self, trues, preds, task_type):
    #     if task_type == 'seq':
    #         acc = accuracy_score(trues, preds)
    #         precision, recall, f1, _ = precision_recall_fscore_support(trues, preds, average='macro')
    #     else:  # token
    #         trues = [item for sublist in trues for item in sublist]
    #         preds = [item for sublist in preds for item in sublist]
    #         acc = accuracy_score(trues, preds)
    #         precision, recall, f1, _ = precision_recall_fscore_support(trues, preds, average='macro')
    #     return acc, precision, recall, f1

# def eval_metric(eval_predict):
#     predictions, labdels = eval_predict
#     seq_output, token_output = predictions


if __name__ == '__main__':
    config = Config()
    # device = config.device
    # 加载模型和tokenizer
    tokenizer = BertTokenizer.from_pretrained(config.bert_dir_en)
    config.bert_dir = config.bert_dir_en
    model = BertForIntentAndSlot(config)

    # 加载数据
    train_dataset, validate_dataset = None, None
    if config.do_train:
        raw_examples = Processor.get_examples(config.train_path_en, 'train')
        train_features = get_features(raw_examples, tokenizer, config)
        train_dataset = BertDataset(train_features)

        raw_examples = Processor.get_examples(config.validate_path_en, 'train')
        validate_features = get_features(raw_examples, tokenizer, config)
        validate_dataset = BertDataset(validate_features)


    if config.do_test:
        raw_examples = Processor.get_examples(config.test_path_en, 'test')
        test_features = get_features(raw_examples, tokenizer, config)
        test_dataset = BertDataset(test_features)
        # test_loader = DataLoader(test_dataset, batch_size=config.batchsize, shuffle=True)

    if config.do_train:
        print('========================== train ==========================')
        args = TrainingArguments(
            output_dir=config.save_dir_en,
            overwrite_output_dir=True,
            learning_rate=2e-5,
            per_device_train_batch_size=8,
            per_device_eval_batch_size=8,
            num_train_epochs=3,
            weight_decay=0.01,
            # evaluation_strategy="steps",  妈了个逼，不做evaluate了，傻逼transformers
            logging_strategy="steps",
            logging_steps=1,
            use_cpu=True
        )

        trainer = CustomTrainer(
            model=model,
            args=args,
            config=config,
            train_dataset=train_dataset,
            eval_dataset=validate_dataset,
            # compute_metrics=eval_metric,
        )

        trainer.train()

    # if args.do_test:
    #     trainer.test(test_loader)

    # if args.do_predict:
    #     with open('./data/predict.json','r') as fp:
    #         pred_data = eval(fp.read())
    #         for i, p_data in enumerate(pred_data):
    #             text = p_data['text']
    #             print(f'========================== predict example-{i} ==========================')
    #             print('文本：', text)
    #             trainer.predict(text, tokenizer)
    #             print(' ')
