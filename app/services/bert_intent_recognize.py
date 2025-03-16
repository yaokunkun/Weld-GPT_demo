import sys
sys.path.append('/dev_data_2/zkyao/code/Weld-GPT_demo')

import numpy as np
from transformers import BertTokenizer, AutoModelForSequenceClassification
from app.config.config import Args, device
from app.config.config import intent_recognize_config as bert_config
from app.utils.materials import corpus_of_value
from seqeval.metrics.sequence_labeling import get_entities
import torch

args = Args()
device = device
args.device = device

label_list = bert_config['label_list']
tokenizer = BertTokenizer.from_pretrained(bert_config['tokenizer_dir'])
model = AutoModelForSequenceClassification.from_pretrained(bert_config['model_dir'], num_labels=len(label_list))
model.to(device)
model.eval()

def rule_predict(query):
    rag_patterns = ['什么是', '为什么']
    if any(rag_pattern in query for rag_pattern in rag_patterns):
        return 'RAG'
    return model_predict(query)
    
def model_predict(query):
    inputs = tokenizer(query, padding=True, return_tensors="pt")
    inputs.to(device)
    with torch.no_grad():
        outputs = model(**inputs)

    logits = outputs.logits
    predicted_classes = torch.argmax(logits, dim=1)
    prediction = label_list[predicted_classes[0]]
    return prediction

def predict(query):
    return rule_predict(query)

if __name__ == '__main__':
    toy_query = "请问氩弧焊什么时候使用，要注意什么？"
    print(model_predict(toy_query))