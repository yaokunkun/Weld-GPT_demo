import sys
sys.path.append('/dev_data/zkyao/code/Weld-GPT_demo')
import re
import numpy as np
from transformers import BertTokenizer, AutoModelForSequenceClassification
from app.config.config import Args, device
from app.config.config import param_control_config as bert_config
from app.utils.materials import corpus_of_value
from seqeval.metrics.sequence_labeling import get_entities
import torch
from app.connection_pool_for_main import http_client
import httpx
from fastapi import HTTPException
mapping_chinese_num2arab_num = {'点': '.', '零': '0', '一': '1', '壹': '1', '两':'2', '二': '2', '貳': '2', '三': '3', '叁': '3', '四': '4', '肆': '4', '五': '5', '伍': '4','六': '6', '七': '7', '八': '8', '捌': '8', '九': '9', '玖': '9'}


# args = Args()
# device = device
# args.device = device

# label_list = bert_config['label_list']
# tokenizer = BertTokenizer.from_pretrained(bert_config['tokenizer_dir'])
# model = AutoModelForSequenceClassification.from_pretrained(bert_config['model_dir'], num_labels=len(label_list))
# model.to(device)
# model.eval()

def chinese_num2arab_num(query):
    result = ""
    for char in query:
        if char in mapping_chinese_num2arab_num:
            result += mapping_chinese_num2arab_num[char]
        else:
            result += char
    result = result.replace('.0', '')
    return result

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
    voltage_patterns = ['伏', '电压', 'V'] + ['幅', '辐']
    if any(current_pattern in query for current_pattern in current_patterns) and any(voltage_pattern in query for voltage_pattern in voltage_patterns):
        for current_pattern in current_patterns:
            if current_pattern in query:
                current_index = query.find(current_pattern)
                break
        for voltage_pattern in voltage_patterns:
            if voltage_pattern in query:
                voltage_index = query.find(voltage_pattern)
                break
        return 'CURRENT' if current_index > voltage_index else 'VOLTAGE'
    if any(current_pattern in query for current_pattern in current_patterns):
        return 'CURRENT'
    if any(voltage_pattern in query for voltage_pattern in voltage_patterns):
        return 'VOLTAGE'
    return None        

async def rule_predict(query):
    query = chinese_num2arab_num(query)
    query = _exclude_current_number(query)
    number = _extract_number(query)
    measuer = _extract_measure(query)
    if not number or not measuer:
        return None
    up_patterns = ['增加', '加', '扩大', '提升']
    down_patterns = ['减少', '减小', '降低']
    up_down_exclude_patterns = ['到', '至', '为', '成']
    control_patterns = ['设为', '调到', '设置为', '调整为', '调整到', '修改到', '修改为', '设置到']+[up_down_pattern+exclude_pattern for up_down_pattern in up_patterns+down_patterns for exclude_pattern in up_down_exclude_patterns]
    if any(control_pattern in query for control_pattern in control_patterns):
        mode = 'control'
    elif any(up_pattern in query for up_pattern in up_patterns) and all(up_down_exclude_pattern not in query for up_down_exclude_pattern in up_down_exclude_patterns):
        mode = 'up'
    elif any(down_pattern in query for down_pattern in down_patterns) and all(up_down_exclude_pattern not in query for up_down_exclude_pattern in up_down_exclude_patterns):
        mode = 'down'
    else: 
        mode = await model_predict(http_client.client,query)
    return (mode, number, measuer)
    
# def model_predict(query):
#     inputs = tokenizer(query, padding=True, return_tensors="pt")
#     inputs.to(device)
#     with torch.no_grad():
#         outputs = model(**inputs)

#     logits = outputs.logits
#     predicted_classes = torch.argmax(logits, dim=1)
#     prediction = label_list[predicted_classes[0]]
#     return prediction

async def model_predict(client: httpx.AsyncClient, query):
    json_for_bert={"query":query}
    # 直接发起 POST 请求
    response = await client.post("/bert_cn_control", json=json_for_bert)
    # 处理响应
    if response.status_code in [200, 201, 202]:
        return response.json()["predictions"]
    else:
        raise HTTPException(status_code=503, detail="bert_server_lost")

async def predict(query):
    return await rule_predict(query)

if __name__ == '__main__':
    # toy_query = "电流改到3, 现在是18V"
    toy_query = "电压增加3，电流扩大为5"
    print(predict(toy_query))