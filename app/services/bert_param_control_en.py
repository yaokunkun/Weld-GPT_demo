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

# mapping_chinese_num2arab_num = {'点': '.', '零': '0', '一': '1', '壹': '1', '两':'2', '二': '2', '貳': '2', '三': '3', '叁': '3', '四': '4', '肆': '4', '五': '5', '伍': '4','六': '6', '七': '7', '八': '8', '捌': '8', '九': '9', '玖': '9'}


# args = Args()
# device = device
# args.device = device

# label_list = bert_config['label_list']
# tokenizer = BertTokenizer.from_pretrained(bert_config['tokenizer_dir'])
# model = AutoModelForSequenceClassification.from_pretrained(bert_config['model_dir'], num_labels=len(label_list))
# model.to(device)
# model.eval()

# def chinese_num2arab_num(query):
#     result = ""
#     for char in query:
#         if char in mapping_chinese_num2arab_num:
#             result += mapping_chinese_num2arab_num[char]
#         else:
#             result += char
#     result = result.replace('.0', '')
#     return result

def _extract_number(query):
    numbers = re.findall(r'\d+', query)
    if numbers:
        return int(numbers[-1])
    else:
        return None
    
def _exclude_current_number(query):
    """
    从query中移除符合以下结构的部分：now is 21A, from 3A
    \b(now|from)\b.*(\d+)\b(a|v|A|V|amp|vol|安的英文|voltage)\b
    
    其中，单位部分可以不出现或出现一次
    """
    # 构建正则表达式模式
    # 单位部分使用问号使其可选
    pattern = r'\b(now|from)\b.*?(\d+)(\b|\s)*(a|v|A|V|amp|vol|ampere|voltage)?\b'
    
    # 使用sub函数将匹配的部分替换为空字符串
    cleaned_query = re.sub(pattern, '', query)
    
    # 清理多余的空格
    cleaned_query = re.sub(r'\s+', ' ', cleaned_query).strip()
    
    return cleaned_query

def _extract_measure(query):
    current_patterns = [r'\bcurrent\b', r'\bamps?\b', r'\d+\s*A\b']
    voltage_patterns = [r'\bvoltage\b', r'\bvolts?\b', r'\d+\s*V\b']
    
    for pattern in current_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return 'CURRENT'
    
    for pattern in voltage_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return 'VOLTAGE'
    
    return None 

async def rule_predict(query):
    # query = chinese_num2arab_num(query)
    query = _exclude_current_number(query)
    number = _extract_number(query)
    measuer = _extract_measure(query)
    if not number or not measuer:
        return None
    
    control_patterns = [
        r'.*?\bto\b.*?(\d+)',  # 包含to 34V
        r'\b(set|adjust|tune|bring|fix|maintain|hold|change|modify)\b.*?(\d+)',  # 包含control关键词
    ]
    control_negative_patterns = [
        r'.*\bby\b.*?(\d+)(?!\bto\b)',  # 包含by 34V，但不包含to
    ]
    up_patterns = [
        r'\b(increase|add|raise|boost|grow|ramp up|turn up|step up)\b',  # 包含increase、add等关键词
    ]
    down_patterns = [
        r'\b(decrease|reduce|lower|drop|cut|ramp down|turn down|step down)\b', # 包含decrease、reduce等关键词
    ]
    # 先判断control，如果不是，则遇到add、cut等关键词可以放心地判断为up、down
    if any(re.search(pattern, query) for pattern in control_patterns) and not any(re.search(pattern, query) for pattern in control_negative_patterns):
        mode = 'control'
    elif any(re.search(pattern, query) for pattern in up_patterns):
        mode = 'up'
    elif any(re.search(pattern, query) for pattern in down_patterns):
        mode = 'down'
    else: 
        mode = await model_predict(http_client.client,query)
    return (mode, number, measuer)
    
async def model_predict(client: httpx.AsyncClient, query):
    json_for_bert={"query":query}
    # 直接发起 POST 请求
    response = await client.post("/bert_en_control", json=json_for_bert)
    # 处理响应
    if response.status_code in [200, 201, 202]:
        return response.json()["predictions"]
    else:
        raise HTTPException(status_code=503, detail="bert_server_lost")

# def model_predict(query):
#     inputs = tokenizer(query, padding=True, return_tensors="pt")
#     inputs.to(device)
#     with torch.no_grad():
#         outputs = model(**inputs)

#     logits = outputs.logits
#     predicted_classes = torch.argmax(logits, dim=1)
#     prediction = label_list[predicted_classes[0]]
#     return prediction

async def predict(query):
    return await rule_predict(query)

if __name__ == '__main__':
    # toy_query = "电流改到3, 现在是18V"
    toy_query = "cut current to 3 A, now is 18V"
    print(predict(toy_query))