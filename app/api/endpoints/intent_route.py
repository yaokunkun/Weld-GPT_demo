import requests
import json
from app.config import config
from app.services import bert_param_control


def get_rag_response(query):
    # 构建请求的JSON数据
    data = {
        "query": query,
        "mode": "local_kb",
        "kb_name": config.kb_name,
        "top_k": 3,
        "score_threshold": 2,
        "history": [
            {
                "content": "你好，请问你了解电焊知识吗",
                "role": "user"
            },
            {
                "content": "我是电焊领域的专家，很乐意为你解答！",
                "role": "assistant"
            }
        ],
        "stream": False,
        "temperature": 0.7,
        "max_tokens": 1024,
        "prompt_name": "default",
        "return_direct": False
    }

    # 假设请求的URL
    url = config.request_url  # 请替换为实际的API URL

    try:
        # 发送POST请求
        response = requests.post(url, json=data)
        response.raise_for_status()  # 检查请求是否成功

        # 解析响应的JSON数据
        response_json = json.loads(response.json())
        choice = response_json["choices"][0]
        # 提取content字段的值
        content = choice["message"]["content"]
        return content
    except requests.RequestException as e:
        print(f"请求出错: {e}")
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"解析响应数据出错: {e}")

    return '等待RAG响应中...'


def get_control_response(query):
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