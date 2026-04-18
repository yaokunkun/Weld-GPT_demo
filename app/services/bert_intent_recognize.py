import sys
sys.path.append('/dev_data/zkyao/code/Weld-GPT_demo')
import re
import numpy as np
from transformers import BertTokenizer, AutoModelForSequenceClassification
from app.config.config import Args, device
from app.config.config import intent_recognize_config as bert_config
from app.utils.materials import corpus_of_value, number_values
from seqeval.metrics.sequence_labeling import get_entities
import torch
import string
from app.connection_pool_for_main import http_client
import httpx
from fastapi import HTTPException

number_values_list = sum([value for value in number_values.values()], [])
corpus_of_value_list =  sum([value for value in corpus_of_value.values()], [])
corpus_list = number_values_list + corpus_of_value_list

# args = Args()  #冗余
# device = device
# args.device = device  #冗余

# label_list = bert_config['label_list']
# tokenizer = BertTokenizer.from_pretrained(bert_config['tokenizer_dir'])
# model = AutoModelForSequenceClassification.from_pretrained(bert_config['model_dir'], num_labels=len(label_list))
# model.to(device)
# model.eval()

#1212厚度判断hotfix +100行
def match_length(text, lang=None):
    results = []
    # 定义不同语言的上下文关键词
    # if lang == 'cn' or (lang is None and any(c in text for c in "厚度个厚宽高长")):
        # 中文关键词
    context_keywords_before = ['厚度', '厚', '薄', '宽', '宽度', '高', '高度', '长', '长度']
    context_keywords_after = ['厚', '薄', '宽', '高', '长', '个厚', '公分']  # 用于"7个厚"这类表达
        # 中文检查范围较小
    before_check_range = 5  # 检查前面字符数量
    after_check_range = 5    # 检查后面字符数量
    #else:
    #    # 英文关键词
    #    context_keywords_before = ['thickness', 'thick', 'thin']
    #    context_keywords_after = ['thick', 'thin', 'wide']
    #    # 英文检查范围稍大
    #    before_check_range = 15  # 检查前面字符数量
    #    after_check_range = 12   # 检查后面字符数量   
    # 匹配所有可能的数字+单位组合
    all_matches = list(re.finditer(r'\b(\d+(?:\.\d+)?)\s*(mm|cm|毫米|厘米)?\b', text, re.IGNORECASE))    
    for match in all_matches:
        start, end = match.start(), match.end()
        value = float(match.group(1))
        explicit_unit = match.group(2)        
        # 确定单位
        if explicit_unit:
            unit = explicit_unit.lower()
            if unit in ['毫米', 'mm']:
                unit = 'mm'
            elif unit in ['厘米', 'cm']:
                unit = 'cm'
            else:
                continue  # 跳过不支持的单位
        else:
            unit = None        
        # 检查是否有上下文（在合理范围内）
        has_context = False        
        # 检查前面的文本
        start_check = max(0, start - before_check_range)
        before_text = text[start_check:start]        
        # 检查后面的文本
        end_check = min(len(text), end + after_check_range)
        after_text = text[end:end_check]       
        # 检查前文关键词
        for keyword in context_keywords_before:
            if keyword in before_text:
                # 确保关键词与数字之间没有句号、换行等分隔符
                keyword_pos = before_text.rfind(keyword)
                between_text = before_text[keyword_pos + len(keyword):]
                if not re.search(r'[。.！!\n\?？]', between_text):  # 没有句子分隔符
                    has_context = True
                    break        
        # 检查后文关键词（如"7个厚"）
        if not has_context:
            for keyword in context_keywords_after:
                if keyword in after_text:
                    # 确保关键词紧随数字或只隔几个字符
                    keyword_pos = after_text.find(keyword)
                    between_text = after_text[:keyword_pos]
                    # 允许数字和关键词之间有少量字符（如空格、"个"等）
                    if len(between_text.strip()) <= 2 and not re.search(r'[。.！!\n\?？]', between_text):
                        has_context = True
                        break        
        # 确定最终结果
        if explicit_unit:  # 有明确单位
            results.append((value, unit))
        elif has_context:  # 无单位但有上下文
            results.append((value, 'mm'))  # 默认单位为mm
        
        if re.fullmatch(r'\d+(\.\d+)?', text.strip()):
            try:
                value = float(text.strip())
                return results.append((value, 'mm'))
            except ValueError:
                return []    
    return results

async def rule_predict(query):
    thickness=match_length(query)
    rag_patterns = ['什么是', '为什么', '怎么办', '如何使用', '怎么使用','介绍','原因','现象','稳定','异响']
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
    #if not thickness and len(query)<8:
    #    return 'QUERY'
    if any(rag_pattern in query for rag_pattern in rag_patterns):
        return 'RAG'

    # 对单独念关键词情况的规则匹配
    if any(query.lower() == corpus.lower() for corpus in corpus_list):
        return 'QUERY'
    clean_query = query.strip(string.punctuation)
    if any(clean_query.lower() == corpus.lower() for corpus in corpus_list):
        return 'QUERY'

    return await model_predict(http_client.client, query, exclude)
    
async def model_predict(client: httpx.AsyncClient, query, exclude):
    json_for_bert={"query":query,"exclude":exclude}
    # 直接发起 POST 请求
    response = await client.post("/bert_cn_classify", json=json_for_bert)
    # 处理响应
    if response.status_code in [200, 201, 202]:
        return response.json()["predictions"]
    else:
        raise HTTPException(status_code=503, detail="bert_server_lost")
    
#def model_predict( query, exclude):    
    # inputs = tokenizer(query, padding=True, return_tensors="pt")
    # inputs.to(device)
    # with torch.no_grad():
    #     outputs = model(**inputs)

    # logits = outputs.logits
    # for item in exclude:
    #     exclude_index = label_list.index(item)
    #     logits[0][exclude_index] = -100
    # predicted_classes = torch.argmax(logits, dim=1)
    # prediction = label_list[predicted_classes[0]]
    # return prediction

async def predict(query):
    return await rule_predict(query)

if __name__ == '__main__':
    # toy_query = "请问氩弧焊什么时候使用，要注意什么？"
    # toy_query = "电压增大8伏"
    # toy_query = "mig5个厚"
    # print(model_predict(toy_query, 'QUERY'))
    toy_query = "方法是氩弧焊，电流要调到几"
    print(predict(toy_query))