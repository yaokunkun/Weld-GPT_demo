import sys
sys.path.append('/dev_data/zkyao/code/Weld-GPT_demo')

import numpy as np
from transformers import BertTokenizer, AutoModelForSequenceClassification
from app.config.config import Args, device
from app.config.config import intent_recognize_config as bert_config
from app.utils.materials import corpus_of_value, number_values
from seqeval.metrics.sequence_labeling import get_entities
import torch
import string

number_values_list = sum([value for value in number_values.values()], [])
corpus_of_value_list =  sum([value for value in corpus_of_value.values()], [])
corpus_list = number_values_list + corpus_of_value_list

args = Args()
device = device
args.device = device

label_list = bert_config['label_list']
tokenizer = BertTokenizer.from_pretrained(bert_config['tokenizer_dir'])
model = AutoModelForSequenceClassification.from_pretrained(bert_config['model_dir'], num_labels=len(label_list))
model.to(device)
model.eval()

def rule_predict(query):
    rag_patterns = ['什么是', '为什么', '怎么办', '如何使用', '怎么使用','介绍']
    exclude = []
    if len(query) > 20:
        exclude.append('CONTROL')
    if any(control_pattern in query for control_pattern in ['电压电流', '电压和电流', '电压与电流', '电流电压']+['如何', '怎样', '怎么']):
        exclude.append('CONTROL')
    if all(control_pattern not in query for control_pattern in ['电压', '电流']):
        exclude.append('CONTROL')
    if any(query_pattern in query for query_pattern in ['调整']):
        exclude.append('QUERY')
    if any(key_word in query for key_word in ['电压', '电流']):
        if any(corpus.lower() in query.lower() for corpus in corpus_list):
            exclude.append('CONTROL')
    if any(rag_pattern in query for rag_pattern in rag_patterns):
        return 'RAG'

    # 对单独念关键词情况的规则匹配
    if any(query.lower() == corpus.lower() for corpus in corpus_list):
        return 'QUERY'
    clean_query = query.strip(string.punctuation)
    if any(clean_query.lower() == corpus.lower() for corpus in corpus_list):
        return 'QUERY'

    return model_predict(query, exclude)
    
def model_predict(query, exclude):
    inputs = tokenizer(query, padding=True, return_tensors="pt")
    inputs.to(device)
    with torch.no_grad():
        outputs = model(**inputs)

    logits = outputs.logits
    for item in exclude:
        exclude_index = label_list.index(item)
        logits[0][exclude_index] = -100
    predicted_classes = torch.argmax(logits, dim=1)
    prediction = label_list[predicted_classes[0]]
    return prediction

def predict(query):
    return rule_predict(query)

if __name__ == '__main__':
    # toy_query = "请问氩弧焊什么时候使用，要注意什么？"
    # toy_query = "电压增大8伏"
    # toy_query = "mig5个厚"
    # print(model_predict(toy_query, 'QUERY'))
    toy_query = "方法是氩弧焊，电流要调到几"
    print(predict(toy_query))