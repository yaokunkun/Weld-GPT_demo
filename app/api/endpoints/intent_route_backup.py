import requests
import json

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


def get_rag_response(query, history_messages, language="cn"):
    base_url = config.request_url
    max_turns = 3
    messages = [
        {"role": "user", "content": "你好，请问你了解电焊知识吗"},
        {"role": "assistant", "content": "我是电焊领域的专家，很乐意为你解答！"},
    ]
    if isinstance(history_messages, list) and len(history_messages) > 0:
        history_messages = history_messages[-max_turns:]
        for history_message in history_messages:
            messages.append({"role": "user", "content": f"{history_message.query}"})
            messages.append({"role": "assistant", "content": f"{history_message.response}"})
    if language == "en":
        query = "Please response in English. " + query
    messages.append({"role": "user", "content": f"{query}"})
    data = {
        "model": "qwen2.5-instruct",
        "messages": messages,
        "stream": True,
        "temperature": 0.7,
        "extra_body": {
            "top_k": 3,
            "score_threshold": 2.0,
            "return_direct": False,
        },
    }
    client = openai.Client(base_url=base_url, api_key="EMPTY")

    # 25.7.4 加入猜你想问，由用户当前问题返回三个推荐问题
    recommend_question_list,_ = question_recommend(query)
    
    try:
        resp = client.chat.completions.create(**data)
        response_text = ""
        for i, chunk in enumerate(resp):
            if i == 0:
                retrieve_docs = chunk.docs
            else:
                chunk_text = chunk.choices[0].delta.content
                response_text += chunk_text
        retrieve_text = ""
        for doc in retrieve_docs:
            doc = doc.replace('\n\n', '\n').strip()
            retrieve_text += f"\n{doc}"
        # 25.7.4 多返回一个推荐问题列表
        return response_text, retrieve_text, recommend_question_list
    except requests.RequestException as e:
        print(f"请求出错: {e}")
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"解析响应数据出错: {e}")

    return '等待RAG响应中...', '',[]


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
    base_url = "http://192.168.2.250:7861/knowledge_base/local_kb/问题推荐示例"
    client = openai.Client(base_url=base_url, api_key="EMPTY")
    client_get_question = OpenAI(base_url="http://192.168.2.250:9997/v1", api_key="not used actually")

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

    
    