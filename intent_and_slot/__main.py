import os
# os.environ["CUDA_VISIBLE_DEVICES"] = '0'

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.optim import Adam
from transformers import BertTokenizer
from seqeval.metrics.sequence_labeling import get_entities

from config import Args
from model import BertForIntentAndSlot
from dataset import BertDataset
from preprocess import Processor, get_features


class Trainer:
    def __init__(self, model, config):
        self.model = model
        self.config = config
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = Adam(self.model.parameters(), lr=config.lr)
        self.epoch = config.epoch
        self.device = config.device

    def train(self, train_loader):
        global_step = 0
        total_step = len(train_loader) * self.epoch
        self.model.train()
        for epoch in range(self.epoch):
            for step, train_batch in enumerate(train_loader):
                for key in train_batch.keys():
                    train_batch[key] = train_batch[key].to(self.device)
                input_ids = train_batch['input_ids']
                attention_mask = train_batch['attention_mask']
                # token_type_ids = train_batch['token_type_ids']
                seq_label_ids = train_batch['seq_label_ids']
                token_label_ids = train_batch['token_label_ids']

                # 计算输出
                seq_output, token_output = self.model(
                    input_ids,
                    attention_mask,
                    # token_type_ids,
                )

                # slots任务
                active_loss = attention_mask.view(-1) == 1  # 注意力掩码
                active_logits = token_output.view(-1, token_output.shape[2])[active_loss]  # mask输出（shape[2]:last hidden size）
                active_labels = token_label_ids.view(-1)[active_loss]  # mask标签

                seq_loss = self.criterion(seq_output, seq_label_ids)  # seq的loss
                token_loss = self.criterion(active_logits, active_labels)  # token的loss
                loss = seq_loss + token_loss  # 两个loss加和

                self.model.zero_grad()
                loss.backward()
                self.optimizer.step()
                print(f'[train] epoch:{epoch+1} {global_step}/{total_step} loss:{round(loss.item(), 6)}')
                global_step += 1

        self.save(self.config.save_dir, 'model.pt')

    def test(self, test_loader):
        self.model.eval()
        seq_preds = []
        seq_trues = []
        token_preds = []
        token_trues = []
        with torch.no_grad():
            for step, test_batch in enumerate(test_loader):
                for key in test_batch.keys():
                    test_batch[key] = test_batch[key].to(self.device)

                input_ids = test_batch['input_ids']
                attention_mask = test_batch['attention_mask']
                # token_type_ids = test_batch['token_type_ids']

                seq_label_ids = test_batch['seq_label_ids']
                token_label_ids = test_batch['token_label_ids']

                # 计算输出
                seq_output, token_output = self.model(
                    input_ids,
                    attention_mask,
                    # token_type_ids,
                )

                # for sequence
                seq_output = seq_output.detach().cpu().numpy()  # 阻断反向传播，转移到cpu上，转为numpy数据
                seq_output = np.argmax(seq_output, -1)

                seq_label_ids = seq_label_ids.detach().cpu().numpy()
                seq_label_ids = seq_label_ids.reshape(-1)

                seq_preds.extend(seq_output)
                seq_trues.extend(seq_label_ids)

                # for token
                token_output = token_output.detach().cpu().numpy()
                token_output = np.argmax(token_output, -1)

                token_label_ids = token_label_ids.detach().cpu().numpy()
                active_len =  torch.sum(attention_mask, -1).view(-1)  # 掩码剩下的长度
                for length, t_output, t_label in zip(active_len, token_output, token_label_ids):
                    t_output = t_output[1:length-1]
                    t_label = t_label[1:length-1]
                    t_ouput = [self.config.id2ner_label[i] for i in t_output]
                    t_label = [self.config.id2ner_label[i] for i in t_label]
                    token_preds.append(t_ouput)
                    token_trues.append(t_label)

        # 正确率计算
        seq_acc, seq_precision, seq_recall, seq_f1 = self.get_metrices(seq_trues, seq_preds, 'seq')
        seq_report = self.get_report(seq_trues, seq_preds, 'seq')
        token_acc, token_precision, token_recall, token_f1 = self.get_metrices(token_trues, token_preds, 'token')
        token_report = self.get_report(token_trues, token_preds, 'token')

        print(' ')
        print('========================== 意图识别 ==========================')
        print('acc:{}\nprec:{}\nrecall:{}\nf1:{}'.format(
            seq_acc, seq_precision, seq_recall, seq_f1
        ))
        print(' ')
        print(seq_report)
        print('========================== 槽位填充 ==========================')
        print('acc:{}\nprec:{}\nrecall:{}\nf1:{}'.format(
            token_acc, token_precision, token_recall, token_f1
        ))
        print(' ')
        print(token_report)


    def get_metrices(self, trues, preds, mode):
        # 计算正确率等
        if mode == 'seq':
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            acc = accuracy_score(trues, preds)
            precision = precision_score(trues, preds, average='micro')
            recall = recall_score(trues, preds, average='micro')
            f1 = f1_score(trues, preds, average='micro')
        elif mode == 'token':
            from seqeval.metrics import accuracy_score, precision_score, recall_score, f1_score
            acc = accuracy_score(trues, preds)
            precision = precision_score(trues, preds)
            recall = recall_score(trues, preds)
            f1 = f1_score(trues, preds)
        return acc, precision, recall, f1

    def get_report(self, trues, preds, mode):
        # 按标签类别报告正确率
        if mode == 'seq':
            from sklearn.metrics import classification_report
            report = classification_report(trues, preds)
        elif mode == 'token':
            from seqeval.metrics import classification_report
            report = classification_report(trues, preds)
        return report

    def save(self, save_path, save_name):
        torch.save(self.model.state_dict(), os.path.join(save_path, save_name))

    def predict(self, text, tokenizer):
        self.model.eval()
        with torch.no_grad():
            tmp_text = [i for i in text]
            inputs = tokenizer.encode_plus(
                text=tmp_text,
                max_length=self.config.max_len,
                padding='max_length',
                truncation='only_first',
                return_attention_mask=True,
                # return_token_type_ids=True,
                return_tensors='pt'
            )
            for key in inputs.keys():
                inputs[key] = inputs[key].to(self.device)

            input_ids = inputs['input_ids']
            attention_mask = inputs['attention_mask']
            # token_type_ids = inputs['token_type_ids']
            
            # 计算输出
            seq_output, token_output = self.model(
                input_ids,
                attention_mask,
                # token_type_ids,
            )

            # for sequence
            seq_output = seq_output.detach().cpu().numpy()
            seq_output  = np.argmax(seq_output, -1)
            seq_output = seq_output[0]
            seq_output = self.config.id2seq_label[seq_output]
            print('意图：', seq_output)
            # for tokens
            token_output = token_output.detach().cpu().numpy()
            token_output = np.argmax(token_output, -1)
            token_output = token_output[0][1:len(text)-1]
            token_output = [self.config.id2ner_label[i] for i in token_output]
            print('槽位：', str([(i[0],text[i[1]:i[2]+1], i[1], i[2]) for i in get_entities(token_output)]))

            return {'意图': seq_output, 
                    '槽位': [(i[0],text[i[1]:i[2]+1], i[1], i[2]) for i in get_entities(token_output)]}


if __name__ == '__main__':
    args = Args()
    device = args.device

    # 加载分词器
    tokenizer = BertTokenizer.from_pretrained(args.bert_dir)

    # 加载模型
    model = BertForIntentAndSlot(args)
    if not args.do_train or args.continue_train:
        model.load_state_dict(torch.load(args.load_dir, map_location=device))
    model.to(device)

    # 加载数据
    if args.do_train:
        raw_examples = Processor.get_examples(args.train_path, 'train')
        train_features = get_features(raw_examples, tokenizer, args)
        train_dataset = BertDataset(train_features)
        train_loader = DataLoader(train_dataset, batch_size=args.batchsize, shuffle=True)

    if args.do_test:
        raw_examples = Processor.get_examples(args.test_path, 'test')
        test_features = get_features(raw_examples, tokenizer, args)
        test_dataset = BertDataset(test_features)
        test_loader = DataLoader(test_dataset, batch_size=args.batchsize, shuffle=True)

    trainer = Trainer(model, args)

    if args.do_train:
        print('========================== train ==========================')
        trainer.train(train_loader)

    if args.do_test:
        trainer.test(test_loader)

    if args.do_predict:
        with open('./data/predict.json','r') as fp:
            pred_data = eval(fp.read())
            for i, p_data in enumerate(pred_data):
                text = p_data['text']
                print(f'========================== predict example-{i} ==========================')
                print('文本：', text)
                trainer.predict(text, tokenizer)
                print(' ')
