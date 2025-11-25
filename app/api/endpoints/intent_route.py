import requests
import json
import time
import sys
from pathlib import Path

# 获取项目根目录（假设根目录是包含 app 的目录）
root_dir = Path(__file__).resolve().parent.parent.parent.parent  # 向上三级：endpoints → api → app → 根目录
sys.path.append(str(root_dir))

from app.config import config
from app.services import bert_param_control, bert_param_control_en
import openai
from openai import OpenAI
import json
import ast


import re
import requests
from urllib.parse import quote


def parse_media_sequence(input_list):
    media_sequence = []
    
    for item in input_list:
        parts = item.strip().split(' ')
        if len(parts) < 1:
            continue  # 忽略无效条目

        local_url = parts[0]
        original_url = ""  # 默认值

        if len(parts) > 1:
            original_url_candidate = parts[1]
            if original_url_candidate != "None":
                original_url = original_url_candidate
            else:
                original_url = ""

        # 判断媒体类型
        lower_local_url = local_url.lower()
        if any(lower_local_url.endswith(ext) for ext in ['.mp4', '.avi', '.mov', '.flv', '.wmv']):
            media_type = "video"
        elif any(lower_local_url.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']):
            media_type = "image"
        else:
            media_type = "unknown"  

        media_sequence.append({
            "type": media_type,
            "local_url": local_url,
            "original_url": original_url
        })
    
    return media_sequence

def get_rag_response(query, history_messages, language="cn"):
    time.sleep(5)
    base_url = "http://127.0.0.1:7861/knowledge_base/local_kb/多模态知识库1115"
    client = openai.Client(base_url=base_url, api_key="EMPTY")

    #多模态知识库2调用
    data = {
        "model": "qwen2.5-instruct",
        "messages": [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好，我是电焊领域的专家。"},
            {"role": "user", "content": query},
        ],
        "stream": False,
        "max_tokens":4096,
        "temperature": 0.6,
        "extra_body": {
        "top_k": 3,
        "score_threshold": 2.0,
        "return_direct": True,
        },
    }


    resp = client.chat.completions.create(**data)
    resp = json.loads(resp)
    retrieve_texts = resp['docs'][-3:]

    #匹配检索结果中的文件路径
    pattern = r'\[([^\]]+)\.txt\]'

    file_paths = []
    for text in retrieve_texts:
        match = re.search(pattern, text)
        if match:
            file_paths.append(match.group(1)+'_url.txt')

    file_paths = [path.split('/')[-1] for path in file_paths]

    # for path in file_paths:
    #     print(path)

    add_media_url = []
    MEDIA_PROCESSED_URL="http://218.13.138.147:9005/media_url/"

    for path in file_paths:
        encoded_path = quote(path, safe='_.-~')
        url = MEDIA_PROCESSED_URL + encoded_path
        try:
            response = requests.get(url, timeout=100)
            response.raise_for_status()
            add_media_url.append(response.text)
        except Exception as e:
            print(f"获取 {url} 失败: {e}")
            add_media_url.append("")

    # print(add_media_url)

    parsed_media_url = parse_media_sequence(add_media_url)

    #电焊知识库调用
    base_url_1 = "http://127.0.0.1:7861/knowledge_base/local_kb/电焊"
    client_1 = openai.Client(base_url=base_url_1, api_key="EMPTY")


    data_1 = {
        "model": "qwen2.5-instruct",
        "messages": [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好，我是电焊领域的专家。"},
            {"role": "user", "content": query},
        ],
        "stream": False,
        "max_tokens":4096,
        "temperature": 0.6,
        "extra_body": {
        "top_k": 3,
        "score_threshold": 2.0,
        "return_direct": True,
        },
    }


    resp_1 = client_1.chat.completions.create(**data_1)
    resp_1 = json.loads(resp_1)
    retrieve_texts_1 = resp_1['docs'][-3:]


    client_get_question = OpenAI(base_url="http://127.0.0.1:9997/v1", api_key="not used actually")
    prompt = "假设你现在是电焊领域的专家，你需要根据用户当前问题，以及检索出的相关知识来回答问题。\n相关知识：{}\n用户当前问题："

    response = client_get_question.chat.completions.create(
                model="qwen2.5-instruct",
                temperature=0.6,
            max_tokens=2048,
            top_p=0.7,
                messages=[
                    {"role": "system", "content": "你好，我是电焊领域的专家。"},
                    {"role": "user", "content": prompt.format(retrieve_texts+retrieve_texts_1)+query}
                ]
            )
    output = response.choices[0].message.content

    print(parsed_media_url)
    return output, str(retrieve_texts)+"\n"+str(retrieve_texts_1), [], parsed_media_url

def get_control_response(query, language="cn"):
    if language == "cn":
        result = bert_param_control.predict(query)
        if not result:
            return "请提供您需要进行控制的参数，例如：请将电压增大5伏、请将电流减小2安、将电流设置为27安。", ()
        
        if result[0] == 'up':
            mode = '增加'
        elif result[0] == 'down':
            mode = '减少'
        else:
            mode = '设置为'
        if result[2] == 'CURRENT':
            measure = '安的电流'
        else:
            measure = '伏的电压'
        response = f"好的，我知道您想要{mode}{result[1]}{measure}"
        return response, result
    elif language == "en":
        result = bert_param_control_en.predict(query)
        if not result:
            return "Please provide the parameter you want to control, e.g., please increase the voltage by 5 volts, please decrease the current by 2 amps, or set the current to 27 amps.", ()
        
        if result[0] == 'up':
            mode = 'increase'
        elif result[0] == 'down':
            mode = 'decrease'
        else:
            mode = 'set to'
        if result[2] == 'CURRENT':
            measure = 'amps of current'
        else:
            measure = 'volts of voltage'
        response = f"Okay, I understand you want to {mode} {result[1]} {measure}"
        return response, result

# 25.7.2 对用户问题进行推荐
def question_recommend(user_question):
    # 返回：output：[recommend_question_1,recommend_question_2,recommend_question_3]
    # 返回：data_base_related: 示例问题知识库返回的检索结果
    base_url = "http://127.0.0.1:7861/knowledge_base/local_kb/问题推荐示例"
    client = openai.Client(base_url=base_url, api_key="EMPTY")
    client_get_question = OpenAI(base_url="http://127.0.0.1:9997/v1", api_key="not used actually")

    question = user_question
    data = {
        "model": "qwen2.5-instruct",
        "messages": [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好，我是电焊领域的专家。"},
            {"role": "user", "content": question},
        ],
        "stream": False,
        "max_tokens":4096,
        "temperature": 0.6,
        "extra_body": {
        "top_k": 1,
        "score_threshold": 2.0,
        "return_direct": True,
        },
    }


    resp = client.chat.completions.create(**data)
    resp = json.loads(resp)
    recommend_questions = resp['docs'][-3:]

    prompt = "假设你现在是一个相关问题推荐官，你需要根据用户当前问题，以及检索出的相关问题来推荐三个新的相关问题。\n相关问题列表：{}\n用户当前问题："
    response = client_get_question.chat.completions.create(
                model="qwen2.5-instruct",
                temperature=0.6,
            max_tokens=2048,
            top_p=0.7,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt.format(recommend_questions)+question+"\n你推荐的三个新问题需要被放在python块的一个列表[]中，且推荐的三个问题中至少有一个已给出的相关问题。"}
                ]
            )
    output = response.choices[0].message.content
    output = output.split('```python')[-1]
    output = output.split('```')[0]
    output = ast.literal_eval(output)
    data_base_related = recommend_questions

    return output,data_base_related


if __name__ == "__main__":
    query = "什么是氩弧焊"
    print(get_rag_response(query))

    
    