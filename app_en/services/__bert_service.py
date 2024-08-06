import logging
import re

import numpy as np
from transformers import BertTokenizer
from app_en.utils.model import BertForIntentAndSlot
from app_en.config.config import Args, device
from seqeval.metrics.sequence_labeling import get_entities
import torch

args = Args()
device = device
args.device = device

tokenizer = BertTokenizer.from_pretrained(args.bert_dir)
model = BertForIntentAndSlot(args)
params = torch.load(args.load_dir, map_location=device)
# del params['bert.embeddings.position_ids']
model.load_state_dict(params)
model.to(device)

mapping = {'点': '.', '零': '0', '一': '1', '壹': '1', '二': '2', '貳': '2', '三': '3', '叁': '3', '四': '4', '肆': '4', '五': '5', '伍': '4','六': '6', '七': '7', '八': '8', '捌': '8', '九': '9', '玖': '9'}


def predict(text):
    ## 处理特殊的难搞的查询
    instant_intent = None
    instant_slots = None
    if text in ['MIG', 'mig', 'mig.', 'MIG.', 'Mig', 'Mig.']:
        instant_intent = 'QUERY_NO_THICKNESS'
        instant_slots = [('MET', 'MIG',0,2)]
    if text in ['GMAW', 'gmaw', 'gmaw.', 'GMAW.']:
        instant_intent = 'QUERY_NO_THICKNESS'
        instant_slots = [('MET', 'GMAW',0,3)]
    if instant_slots is not None:
        # print('意图：', instant_intent)
        # logging.info(f'意图：{instant_intent}')
        # print('槽位：', instant_slots)
        # logging.info(f'槽位：{instant_slots}')
        return {'意图': instant_intent, '槽位': str(instant_slots)}, True

    ##
    ## 正常的查询
    text = text + "  "
    config = args
    model.eval()
    with torch.no_grad():
        tmp_text = [i for i in text]
        inputs = tokenizer.encode_plus(
            text=tmp_text,
            max_length=config.max_len,
            padding='max_length',
            truncation='only_first',
            return_attention_mask=True,
            # return_token_type_ids=True,
            return_tensors='pt'
        )
        for key in inputs.keys():
            inputs[key] = inputs[key].to(device)

        input_ids = inputs['input_ids']
        attention_mask = inputs['attention_mask']
        # token_type_ids = inputs['token_type_ids']

        # 计算输出
        seq_output, token_output = model(
            input_ids,
            attention_mask,
            # token_type_ids,
        )

        # for sequence
        seq_output = seq_output.detach().cpu().numpy()
        seq_output = np.argmax(seq_output, -1)
        seq_output = seq_output[0]
        seq_output = config.id2seq_label[seq_output]
        intent = seq_output
        # print('意图：', seq_output)
        # logging.info(f'意图：{seq_output}')
        # for tokens
        token_output = token_output.detach().cpu().numpy()
        token_output = np.argmax(token_output, -1)
        token_output = token_output[0][1:len(text) - 1]
        token_output = [config.id2ner_label[i] for i in token_output]
        # print('槽位：', str([(i[0], text[i[1]:i[2] + 1], i[1], i[2]) for i in get_entities(token_output)]))
        # logging.info(f'槽位：{str([(i[0], text[i[1]:i[2] + 1], i[1], i[2]) for i in get_entities(token_output)])}')
        entities = [(i[0], text[i[1]:i[2] + 1], i[1], i[2]) for i in get_entities(token_output)]

        return {'意图': intent,
                '槽位': str(entities)}, False
