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


RAG_MODEL="qwen3.5"
GEN_MODEL="qwen3.5"


def get_rag_response(query, history_messages, language="cn", Enable_thinking=False):
    # max_turns = 3
    messages = [
        {"role": "user", "content": "你好，请问你了解电焊知识吗"},
        {"role": "assistant", "content": "我是电焊领域的专家，很乐意为你解答！"},
    ]
    # print((history_messages))
    if isinstance(history_messages, list) and history_messages:
        # history_messages = history_messages[-max_turns:]
        for history_message in history_messages:
            messages.append({"role": "user", "content": f"{history_message.query}"})
            messages.append({"role": "assistant", "content": f"{history_message.response}"})
            # print(history_message)
    if language == "en":
        query = "Please response in English. " + query
    
    messages_without_query = messages
    messages.append({"role": "user", "content": f"{query}"})
    
    # time.sleep(5)
    base_url = "http://192.168.2.250:7861/knowledge_base/local_kb/多模态知识库1115"
    client = openai.Client(base_url=base_url, api_key="EMPTY")
    #多模态知识库2调用
    data = {
        "model": RAG_MODEL,
        "messages": messages,
        "stream": False,
        "max_tokens":4096,
        "temperature": 0.6,
        "extra_body": {
            "top_k": 20,
            "score_threshold": 0.5,
            "return_direct": True,
            "chat_template_kwargs": {"enable_thinking": False},
        },
    }

    resp = client.chat.completions.create(**data)
    resp = json.loads(resp)
    retrieve_texts = resp['docs'][-20:]
    # print(retrieve_texts)

    #电焊知识库调用
    base_url_1 = "http://192.168.2.250:7861/knowledge_base/local_kb/电焊"
    client_1 = openai.Client(base_url=base_url_1, api_key="EMPTY")
    data_1 = {
        "model": RAG_MODEL,
        "messages": messages,
        "stream": False,
        "max_tokens":4096,
        "temperature": 0.6,
        "extra_body": {
            "top_k": 3,
            "score_threshold": 0.5,
            "return_direct": True,
            "chat_template_kwargs": {"enable_thinking": False},
        },
    }

    resp_1 = client_1.chat.completions.create(**data_1)
    resp_1 = json.loads(resp_1)
    retrieve_texts_1 = resp_1['docs'][-3:]

    
    client_get_question = OpenAI(base_url="http://192.168.2.250:8010/v1", api_key="not used actually")

    prompt = '''
        （请不要进行长时间思考，快速回答问题）

        你是一名电焊领域的技术专家，请从用户提出的问题中精准识别并提取所有**具体的电焊相关专业术语**作为关键词。

        要求：
        - 提取出来的关键词数量不限，若关键词长度大于3，则拆分为严格小于等于3的关键词！！英文除外
        - **提取以下类别的术语**：
        - 具体焊接工艺（如：气保焊、氩弧焊、手工焊、埋弧焊、激光焊等）
        - 焊接设备或工具（如：焊枪、送丝机、焊机等）
        - 焊接材料（如：铝镁、合金、焊条等）
        - 缺陷类型（如：气孔、未熔合、咬边、裂纹等）
        - 工艺参数（如：电流、电压、干伸长等）
        - **严格排除以下内容**：
        - 泛化词汇：如“电焊”“焊接”“焊”“焊工”等常见通用词；
        - 通用动词、疑问词、助词（如“怎么”“如何”“解决”“使用”等）；
        - 输出必须为标准 JSON 格式，仅包含一个字段 "keywords"，其值为字符串数组；
        - 若无符合要求的术语，返回空数组；
        - 尽量将复合词拆分为最小有效专业单元（例如：“铝镁焊丝” → ["铝镁", "焊丝"]）；
        - 不要解释、不要额外文本，只输出 JSON。
        
        示例1：
        输入：气保焊可以焊接哪些材料？
        输出：
        {
            "keywords": ["气保焊"]
        }

        示例2：
        输入：手工焊和氩弧焊的区别是什么？
        输出：
        {
            "keywords": ["手工焊", "氩弧焊"]
        }

        示例3：
        输入：为什么TIG焊容易出现气孔？
        输出：
        {
            "keywords": ["TIG", "气孔"]
        }

        示例4：
        输入：电焊时怎么防止飞溅？
        输出：
        {
            "keywords": ["飞溅"]
        }

        示例5：
        输入：焊接的基本原理是什么？
        输出：
        {
            "keywords": []
        }

        当前用户问题：
        '''

    # print(prompt+query)
    
    response = client_get_question.chat.completions.create(
        model=GEN_MODEL,
        temperature=0.6,
        max_tokens=4096,
        top_p=0.7,
        messages=[
            {"role": "system", "content": "你好，我是电焊领域的专家。"},
            {"role": "user", "content": prompt+query}
        ],
        extra_body={
            "chat_template_kwargs": {"enable_thinking": False}
        }
    )
    
    print(prompt+query)
    output = response.choices[0].message.content

    required = json.loads(output)
    required = required["keywords"]
    print(retrieve_texts)
    print(f"大模型识别出的关键词{required}")

    if required:
        retrieve_texts = [
            doc for doc in retrieve_texts 
            if any(kw.lower() in doc.lower() for kw in required)
        ]

    retrieve_texts = retrieve_texts[0:3]
    print(retrieve_texts)
    
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


    prompt = '''        
        <思考模式注意事项>在进行内部思考（Thinking）时，务必保持精简，仅提取核心逻辑，禁止冗长的发散或自我重复，思考所使用的token严格控制在**500以内**。
        </思考模式注意事项结束>
        
        <回答问题注意事项>你是一个能够控制智能焊机的大模型，如果用户提问与参考问题高度相关，请严格参考以下示例词语进行回答，并且不要回答其他在参考回答中没有出现的内容或进行联想；
        若与参考问题无关，请不要参考以下示例：
        问题1：焊接方法有什么？\我可以选择哪些焊接方法？
        目前可使用焊接方法：['MIG', 'MMA', 'tig_ac', 'tig_dc']
        
        问题2：焊接材料有什么？\我可以选择哪些焊接材料？
        目前可使用焊接材料：['FE', 'CUSI', 'ALMG', 'FLUX', 'STEEL', 'ALSI']
        </回答问题注意事项结束>
        
        <口音纠正注意事项>
        你是一个专门回答电焊相关问题的大模型，用户输入可能包含口音或语音转文字错误（如 n/l 不分、u/ü 混淆）。请结合语境，将“怪异词汇”还原为最可能的正确词汇后再回答。
        纠错对照参考：
        【铝/合金相关】：女美、旅美 → 铝镁；女归 → 铝硅；驴 → 铝。
        【术语相关】：mi狙、mi居、mi区、ma区、mag→ mig。
        <口音纠正注意事项结束>
        
        <回复格式注意事项>
        1. 禁止自称：请直接回答问题，**绝对不要**在回复中自称“专家”、“作为电焊领域的专家”或使用类似的身份开场白，除非用户特别提问介绍你自己。
        2. 隐蔽检索过程：你需要结合相关知识来回答问题。如果发现“相关知识”与当前问题无关，请直接忽略它并给出解答。**严禁**在回复中输出“检索出的内容不相关”、“提供的资料中没有”等暴露系统检索机制失效的词句。
        <回复格式注意事项结束>
        
        假设你现在是电焊领域的专家，你需要根据用户当前问题，结合历史对话内容，以及检索出的相关知识来回答问题。
        历史对话：{}
        相关知识：{}
        
        用户当前问题：
    '''
    
    
    print(prompt.format(messages_without_query, str(retrieve_texts+retrieve_texts_1))+query)
    response = client_get_question.chat.completions.create(
        model=GEN_MODEL,
        temperature=0.6,
        max_tokens=128000,
        top_p=0.7,
        messages=[
            {"role": "system", "content": "你是电焊领域的专家，请解答用户的问题。"},
            {"role": "user", "content": prompt.format(messages_without_query, str(retrieve_texts+retrieve_texts_1))+query}
        ],
        extra_body={
            "chat_template_kwargs": {"enable_thinking": Enable_thinking}
        },
        presence_penalty=0.6
    )
    output = response.choices[0].message.content
    thinking_output = ''
    if(Enable_thinking): thinking_output = response.choices[0].message.reasoning
    # print(response)
    output += f"\n\nAI生成"

    # print(parsed_media_url)
    return output, thinking_output, str(retrieve_texts)+"\n"+str(retrieve_texts_1), [], parsed_media_url





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

    
    