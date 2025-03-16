import sys
sys.path.append('/dev_data_2/zkyao/code/Weld-GPT_demo')
import re
import numpy as np
from transformers import BertTokenizer, AutoModelForSequenceClassification
from app.config.config import Args, device
from app.config.config import param_control_config as bert_config
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

def _extract_number(query):
    numbers = re.findall(r'\d+', query)
    if numbers:
        return int(numbers[-1])
    else:
        return None
    
def _exclude_current_number(query):
    patterns = ['现在是', '现在为', '目前']
    end_patterns = ['.', ',', '，', '。', 'A', 'V', '安', '伏']
    for pattern in patterns:
        if pattern in query:
            start_index = query.rfind(pattern)
            for end_pattern in end_patterns:
                if end_pattern in query[start_index:]:
                    end_index = query.find(end_pattern, start_index)
                    return query[:start_index]+query[end_index+len(end_pattern):]
            return query[:start_index]
    return query

def _extract_measure(query):
    current_patterns = ['安', '电流', 'A']
    voltage_patterns = ['伏', '电压', 'V']
    if any(current_pattern in query for current_pattern in current_patterns):
        return 'CURRENT'
    if any(voltage_pattern in query for voltage_pattern in voltage_patterns):
        return 'VOLTAGE'
    return None        

def rule_predict(query):
    query = _exclude_current_number(query)
    number = _extract_number(query)
    measuer = _extract_measure(query)
    if not number or not measuer:
        return None
    up_patterns = ['增加', '加', '扩大', '提升']
    down_patterns = ['减少', '减小', '降低']
    up_down_exclude_patterns = ['到', '至', '为']
    control_patterns = ['设为', '调到', '设置为', '调整为', '调整到', '修改到', '修改为', '设置到']
    if any(up_pattern in query for up_pattern in up_patterns) and all(up_down_exclude_pattern not in query for up_down_exclude_pattern in up_down_exclude_patterns):
        mode = 'up'
    elif any(down_pattern in query for down_pattern in down_patterns) and all(up_down_exclude_pattern not in query for up_down_exclude_pattern in up_down_exclude_patterns):
        mode = 'down'
    elif any(control_pattern in query for control_pattern in control_patterns):
        mode = 'control'
    else: 
        mode = model_predict(query)
    return (mode, number, measuer)
    
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
    toy_query = "电流改到3, 现在是18V"
    print(predict(toy_query))