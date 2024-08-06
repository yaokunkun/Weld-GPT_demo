import os
import requests
import json
import re
import pandas as pd

def parse_result(result):
    # 初始化变量为空字符串
    thickness = ""
    material = ""
    method = ""

    # 匹配并提取 "焊接厚度是" 后面的内容直到逗号
    thickness_match = re.search(r"焊接厚度是([^，。]+)", result)
    if thickness_match:
        thickness = thickness_match.group(1).strip()

    # 匹配并提取 "焊接材料是" 后面的内容直到逗号
    material_match = re.search(r"焊接材料是([^，。]+)", result)
    if material_match:
        material = material_match.group(1).strip()
    # 匹配并提取 "焊接方法是" 后面的内容直到逗号或句号
    method_match = re.search(r"焊接方法是([^，。]+)", result)
    if method_match:
        method = method_match.group(1).strip()
    return thickness, material, method



def process_text_files(directory):
    city = directory[-2:]
    print(f"正在处理城市{city}")
    fr = open(os.path.join(directory, f'{city}_text.txt'), 'r', encoding='utf-8')
    texts = [line.strip() for line in fr.readlines()]
    datas = []
    for text in texts:
        data = {'讯飞转出文本': text}
        response = requests.post("http://202.38.247.12:8003/api/session/start").content.decode('utf-8')
        response_dict = json.loads(response)
        session_id = response_dict['session_id']
        response = requests.post(f"http://202.38.247.12:8003/api/session/{session_id}/?query={text}").content.decode('utf-8')
        response_dict = json.loads(response)
        fixed_query = response_dict['fixed_query']
        result = response_dict['response']
        if not isinstance(result, str):
            result = result['response']
        thickness, material, method = parse_result(result)
        data['后端纠正后的文本'] = fixed_query
        data['thickness'] = thickness
        data['material'] = material
        data['method'] = method
        datas.append(data)
    df = pd.DataFrame(datas)
    df.to_excel(os.path.join(directory, f'{city}.xlsx'), index=False)

if __name__ == "__main__":
    directories = [
        '/dev_data_2/zkyao/code/Weld-GPT_demo/app/api/endpoints/第一期语音文件/东北',
        '/dev_data_2/zkyao/code/Weld-GPT_demo/app/api/endpoints/第一期语音文件/山东',
        '/dev_data_2/zkyao/code/Weld-GPT_demo/app/api/endpoints/第一期语音文件/河南',
        '/dev_data_2/zkyao/code/Weld-GPT_demo/app/api/endpoints/第一期语音文件/随州',
        '/dev_data_2/zkyao/code/Weld-GPT_demo/app/api/endpoints/第一期语音文件/麻城'
    ]
    for directory in directories:
        process_text_files(directory)
