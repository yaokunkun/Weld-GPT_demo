import numpy as np
from transformers import BertTokenizer, AutoModelForTokenClassification
from app_en.config.config import Args, device
from app_en.utils.materials import corpus_of_value
from seqeval.metrics.sequence_labeling import get_entities
import torch

args = Args()
device = device
args.device = device

tokenizer = BertTokenizer.from_pretrained(args.bert_dir)
model = AutoModelForTokenClassification.from_pretrained(args.load_dir)
model.to(device)


def get_unit_intent(text):
    for x in ["厘米", "公分", "cm", "CM"]:
        if x in text:
            return "QUERY_CM"
    return "QUERY_MM"

def check_MET(value):
    value_list = corpus_of_value['MET']
    return True if value in value_list else False

def predict(text):
    config = args
    model.eval()
    with torch.no_grad():
        text = text.lower()
        inputs = tokenizer.encode_plus(
            text=text,
            max_length=config.max_len,
            padding='max_length',
            truncation='only_first',
            return_attention_mask=True,
            return_tensors='pt'
        )
        for key in inputs.keys():
            inputs[key] = inputs[key].to(device)

        input_ids = inputs['input_ids']
        attention_mask = inputs['attention_mask']

        # 计算输出
        output = model(input_ids, attention_mask)
        output = output.logits.detach().cpu().numpy()
        output = np.argmax(output, -1)
        output = output[0]
        output = [config.id2ner_label[i] for i in output]
        entities = [(i[0], input_ids[0][i[1]:i[2] + 1], i[1], i[2]) for i in get_entities(output)]  # 重点：是拿input_ids和output的logits对应，可千万别拿text[1:-1]去对应
        decoded_entities = []
        for entity in entities:
            entity_list = list(entity)
            entity_list[1] = tokenizer.decode(entity[1])  # 注意，中文模型要.replace(' ', '')，英文是不加的，应为英文单词之间得空格
            # 如果焊接方法不在语料库里，刨掉
            if entity_list[0] == 'MET':
                if check_MET(entity_list[1]):
                    decoded_entities.append(tuple(entity_list))
                elif entity_list[1] not in ['[CLS]', '[SEP]']:  # 有时候会抽风，把这两个东西标注为实体
                    decoded_entities.append(tuple(entity_list))
        print(decoded_entities)

        return {'意图': get_unit_intent(text),
                '槽位': str(decoded_entities)}

if __name__ == "__main__":
    text = "my welding method is mig, welding material is steel, please tell me what parameters i need."
    print(predict(text))