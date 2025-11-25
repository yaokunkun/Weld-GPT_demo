from app.utils.paramSQL import get_all_MET, get_all_MAT, get_all_THI, get_all_param_by_MAT_MET,select_user_THI
from app.utils import paramSQL
from app.utils import userParamSQL
from app.utils.materials import corpus_of_value
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
import torch
import numpy as np

def linear_fit_and_predict(data, x):
    # 分离二维元组列表中的 x 和 y 值
    x_values = np.array([point[0] for point in data])
    y_values = np.array([point[1] for point in data])

    # 进行线性拟合，得到斜率和截距
    slope, intercept = np.polyfit(x_values, y_values, 1)

    # 定义线性方程
    def linear_equation(x):
        return slope * x + intercept

    # 使用线性方程预测给定 x 对应的 y 值
    predicted_y = linear_equation(x)

    return predicted_y

def linear_interpolation(data, x):
    # 对数据按照 x 值排序
    sorted_data = sorted(data, key=lambda point: point[0])
    # 找到最接近的两个点
    for i in range(len(sorted_data) - 1):
        if sorted_data[i][0] <= x <= sorted_data[i + 1][0]:
            x1, y1 = sorted_data[i]
            x2, y2 = sorted_data[i + 1]
            # 线性插值公式
            y = y1 + (y2 - y1) * (x - x1) / (x2 - x1)
            return y
    # 如果 x 不在已有值的区间里
    return linear_fit_and_predict(data, x)

# corpus_of_MAT = corpus_of_value['MAT']
corpus_of_MAT = ['Al-99.5']

materials_map = {
    'Al-Si-4': 'AlSi',
    '铝铁合金': '铝镁合金',
    '碳钢': 'Steel',
    'Al-Si-5': 'AlSi',
}

material_recommend_sentence_with_map = "好的，我已经知道了焊接方法是{MET}，焊接厚度是{THI}。您提供的焊接材料是{MAT}，系统推荐您采用{new_MAT}的参数。"
material_recommend_sentence_without_map = "好的，我已经知道了焊接方法是{MET}，焊接厚度是{THI}。您提供的焊接材料是{MAT}，由于数据库中暂无该材料的数据，根据检索系统建议您采用{new_MAT}的参数。"
thickness_recommend_sentence = "由于官方和您的数据库中暂无{THI}厚度的数据，经过现有的官方数据计算为您推荐以下参数。"
user_thickness_recommend_sentence = "数据库中在焊接方法是{MET},焊接材料是{MAT}的条件下没有您提供的{THI}厚度数据，且无官方数据支持，但是有以下自定义厚度数据可以使用"

tokenizer = AutoTokenizer.from_pretrained('/dev_data/zkyao/pretrain_model/bge-large-zh-v1.5')
model = AutoModel.from_pretrained('/dev_data/zkyao/pretrain_model/bge-large-zh-v1.5')

def formulate_result_dict(result_dict):
    """_summary_

    Args:
        result_dict: 厚度推荐返回的结果格式 
        {
            0.8: {
                "Feeder creep speed": 2.7,
                "ArcingCurrent": 360,
                "ArcingTime": 4,...
            }
        }
    Return: 对齐到机械学院的格式
        {
            "WireDiameter:0.8": [
                {
                    "Feeder creep speed": "2.7"
                },
                {
                    "ArcingCurrent": "360"
                },
                {
                    "ArcingTime": "4"
                },...
            ],...
        }

    """
    new_dict = {}
    for DIA, params_this_DIA in result_dict.items():
        new_dict_key = f"WireDiameter:{DIA}"
        new_dict_list = []
        for param_name, param_value in params_this_DIA.items():
            new_dict_list.append({param_name: str(param_value)})
        new_dict[new_dict_key] = new_dict_list
    return new_dict
    
def get_embeddings(texts):
    inputs = tokenizer(texts, padding=True, truncation=True, return_tensors='pt')
    with torch.no_grad():
        outputs = model(**inputs)
    # 取 [CLS] 标记的输出作为句子的表示
    embeddings = outputs.last_hidden_state[:, 0, :].numpy()
    return embeddings

corpus_embeddings = get_embeddings(corpus_of_MAT)


def rule_recommend(MAT):
    return materials_map.get(MAT, "AlMg")  # TODO

def model_recommend(MAT):
    input_embedding = get_embeddings([MAT])
    similarities = cosine_similarity(input_embedding, corpus_embeddings)[0]
    most_similar_index = np.argmax(similarities)
    return corpus_of_MAT[most_similar_index]

def material_recommend(MAT):
    result = rule_recommend(MAT)
    if result:
        return 'RULE', result
    else:
        return 'MODEL', model_recommend(MAT)
    
def thickness_recommend(MAT, MET, THI):
    # all_params = get_all_param_by_MAT_MET(MET, MAT)
    # all_params_dict_index = {}  # 本轮目标：{DIA: {index: {paramName: paramValue}}}  index与THI一一对应
    # for DIA, paramName, paramValue, ParamIndex in all_params:
    #     if DIA not in all_params_dict_index:
    #         all_params_dict_index[DIA] = {}
    #     if ParamIndex not in all_params_dict_index[DIA]:
    #         all_params_dict_index[DIA][ParamIndex] = {}
    #     all_params_dict_index[DIA][ParamIndex][paramName] = paramValue

    # all_params_dict = {}  # 本轮目标：{DIA: {THI: {paramName: paramValue}}}  index与THI一一对应
    # for DIA, dict_of_this_DIA in all_params_dict_index.items():
    #     all_params_dict[DIA] = {}
    #     for param_index, dict_of_this_DIA_index in dict_of_this_DIA.items():
    #         all_params_dict[DIA][dict_of_this_DIA_index['Guideline value for material']] = dict_of_this_DIA_index
            
    # processed_params_dict = {}  # 本轮目标：{DIA: {paramName: [(THI, paramValue)]}}
    # for DIA, params_THI_dict in all_params_dict.items():
    #     new_list_dict = {}
    #     for _THI, params_this_DIA_THI in params_THI_dict.items():
    #         if _THI == '-100':
    #             continue
    #         for paramName, paramValue in params_this_DIA_THI.items():
    #             if paramName not in new_list_dict:
    #                 new_list_dict[paramName] = []
    #             new_list_dict[paramName].append((float(_THI), float(paramValue)))
    #     # 存储的-100占位参数，不放进最终结果
    #     if new_list_dict:
    #         processed_params_dict[DIA] = new_list_dict

    processed_params_dict = {}  # 目标格式：{DIA: {paramName: [(THI, paramValue)]}}
    all_params = get_all_param_by_MAT_MET(MAT=MAT, MET=MET)
    # [('0', '0.8', 'AUTOSetSpeed', '20'),
    #  ('0', '1', 'AUTOSetSpeed', '20'),
    #  ('0', '0.8', 'CraterOffTime', '0')]
    for thi, dia, name, value in all_params:
        if dia not in processed_params_dict:
            processed_params_dict[dia] = {}
        if name not in processed_params_dict[dia]:
            processed_params_dict[dia][name] = []
        processed_params_dict[dia][name].append((float(thi), float(value)))
    # {
    #     '0': {
    #         'AUTOSetSpeed': [(0.8, 20.0), (1.0, 20.0), ...],
    #         'CraterOffTime': [(0.8, 0.0), (1.0, 1.0), ...],
    #         ...
    #     },
    # }
    
    # 对于已解析的结果，进行线性预测
    result_dict = {}
    for DIA, params_dict_of_this_DIA in processed_params_dict.items():
        result_dict[DIA] = {}
        for param_name, data in params_dict_of_this_DIA.items():
            predict_param_value = linear_interpolation(data=data, x=float(THI))
            result_dict[DIA][param_name] = round(predict_param_value, 2)
    # {
    #     '0': {
    #         'AUTOSetSpeed': 20.0,
    #         'CraterOffTime': 0.5,
    #         ...
    #     },
    # }
    return result_dict

def recommend(MAT, MET, THI, userID):
    """
    return: dict: {"response": response_sentence, "data": result_dict}
    """
    response = ""
    # 1.先看对应的（材料，方法）下数据库有没有数据
    all_THI = get_all_THI(userID=userID, MET=MET, MAT=MAT)
    official_param = get_all_param_by_MAT_MET(MET=MET, MAT=MAT)
    user_THI = select_user_THI(MET=MET, MAT=MAT,userID=userID)
    #1.1 新焊接方法新推荐方法
    if MET.upper()=="MMA":
        return rec_mma(MAT, THI)
    if MET.upper()=="TIG_DC":
        return rec_tig_dc(THI)
    if MET.upper()=="TIG_AC":
        return rec_tig_ac(THI)
    # 2.如果没有，走材料推荐
    if len(all_THI) == 0:
        rec_type, new_MAT = material_recommend(MAT)
        response += material_recommend_sentence_with_map.format(MET=MET, THI=THI, MAT=MAT, new_MAT=new_MAT) if rec_type == 'RULE' else material_recommend_sentence_without_map.format(MET=MET, THI=THI, MAT=MAT, new_MAT=new_MAT)
        MAT = new_MAT
    #2.1. 如果查询到数据为用户私有数据，直接返回用户厚度。
    elif len(user_THI)!=0 and len(official_param)==0:
        response +=user_thickness_recommend_sentence.format(MET=MET, THI=THI, MAT=MAT)
        return{"response":response, "data":user_THI}
    # 3.进行二次查询
    result_dict = paramSQL.select_SQL(MET, MAT, THI)
    # 4.如果没有数据，再走厚度推荐
    if len(result_dict) == 0:
        result_dict = thickness_recommend(MAT, MET, THI)
        result_dict = formulate_result_dict(result_dict)
        response += thickness_recommend_sentence.format(THI=THI)
        return {"response": response, "data": result_dict}
    # 5. 查询结果解析
    '''
    new_result_dict = {}
    for diameter, dataIndexList in result_dict.items():
        # 遍历公共数据表中每组焊丝直径和对应的参数list
        for dataIndex in dataIndexList:
            # 遍历所有参数list
            paramName, paramValue = paramSQL.select_by_ID(dataIndex)[0]
            if diameter not in new_result_dict:
                new_result_dict[diameter] = []
            new_result_dict[diameter].append({paramName: paramValue})
    '''
    new_result_dict = {}
    for Diameter, ParamName, ParamValue in result_dict:
            DiameterO=f"WireDiameter:{Diameter}"
            if DiameterO not in new_result_dict:
                new_result_dict[DiameterO] = []
            new_result_dict[DiameterO].append({ParamName: ParamValue})
    return {"response": response, "data": new_result_dict}
#         {
#             "WireDiameter:0.8": [
#                 {
#                     "Feeder creep speed": "2.7"
#                 },
#                 {
#                     "ArcingCurrent": "360"
#                 },
#                 {
#                     "ArcingTime": "4"
#                 },...
#             ],...
#         }


def rec_mma(MAT, THI):
    curr=(float(THI)*10.0-20)*2+30.0
    curr=max(30.0,curr)
    curr=min(500.0,curr)
    if (curr<90.0): dia=2.0
    elif (curr<120.0): dia=2.5
    elif (curr<160.0): dia=3.2
    elif (curr<230.0): dia=4.0
    elif (curr<300.0): dia=5.0
    elif (curr<=500.0): dia=6.0
    return {"response": f"您查询的MMA焊接方法,焊接材料是{MAT},焊接厚度是{THI}的推荐参数如下,WireDiameter指的是焊条宽度",
            "data": {
                "WireDiameter:{}".format(dia): [
                    {"MMASetCurrent": "{}".format(curr)}
                    ]
                }
            }
    
    
def rec_tig_dc(THI):
    curr=float(THI)*30.0
    curr=max(curr,20)
    curr=min(curr,500)
    dia=2
    if curr<20: dia=0.5
    elif curr<70: dia=1.0
    elif curr<125: dia=1.6
    elif curr<180: dia=2.0
    elif curr<240: dia=2.5
    elif curr<=340: dia=3.2
    elif curr<=490: dia=4.0
    elif curr<=660: dia=5.0
    elif curr<=950: dia=6.3
    return {"response": f"您查询的TIG_DC 焊接方法,焊接材料只能是不锈钢(STEEL),焊接厚度是{THI}的推荐参数如下,注意:这里的WireDiameter指的是直流正接(电极-)条件下钍钨电极的直径",
            "data": {
                "WireDiameter:{}".format(dia): [
                    {"StraightDC_TIGSetCurrent": "{}".format(curr)}
                    ]
                }
            }
    
    
    
def rec_tig_ac(THI):
    curr=float(THI)*40.0
    curr=max(curr,20)
    curr=min(curr,500)
    if  curr<15: dia=0.5
    elif curr<50: dia=1.0
    elif curr<75: dia=1.6
    elif curr<100: dia=2.0
    elif curr<145: dia=2.5
    elif curr<=185: dia=3.2
    elif curr<=250: dia=4.0
    elif curr<=325: dia=5.0
    elif curr<=450: dia=6.3
    elif curr<=500: dia=8.0
    return {"response": f"您查询的TIG_AC 焊接方法,焊接材料只能是铝(AL),焊接厚度是{THI}的推荐参数如下,注意:这里的WireDiameter指的是交流条件下钍钨电极的直径",
            "data": {
                "WireDiameter:{}".format(dia): [
                    {"AC_TIGSetCurrent": "{}".format(curr)}
                    ]
                }
            }