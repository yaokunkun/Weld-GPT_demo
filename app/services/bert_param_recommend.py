from app.utils.paramSQL import get_all_MET, get_all_MAT, get_all_THI
from app.utils import paramSQL
from app.utils import userParamSQL
from app.utils.materials import corpus_of_value
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
import torch
import numpy as np

# corpus_of_MAT = corpus_of_value['MAT']
corpus_of_MAT = ['Al-99.5']

materials_map = {
    'Al-Si-4': 'Al-Si-5',
    '铝铁合金': '铝镁合金'
}

material_recommend_sentence_with_map = "您提供的焊接材料是{MAT}，系统推荐您采用{new_MAT}的参数。"
material_recommend_sentence_without_map = "您提供的焊接材料是{MAT}，由于数据库中暂无该材料的数据，根据检索系统建议您采用{new_MAT}的参数。"
thickness_recommend_sentence = "提供的焊接厚度是{THI}，参数由系统推荐计算。"

tokenizer = AutoTokenizer.from_pretrained('/dev_data/zkyao/pretrain_model/bge-large-zh-v1.5')
model = AutoModel.from_pretrained('/dev_data/zkyao/pretrain_model/bge-large-zh-v1.5')
def get_embeddings(texts):
    inputs = tokenizer(texts, padding=True, truncation=True, return_tensors='pt')
    with torch.no_grad():
        outputs = model(**inputs)
    # 取 [CLS] 标记的输出作为句子的表示
    embeddings = outputs.last_hidden_state[:, 0, :].numpy()
    return embeddings

corpus_embeddings = get_embeddings(corpus_of_MAT)


def rule_recommend(MAT):
    return materials_map.get(MAT, None)

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
    
def thickness_recommend():
    pass

def recommend(MAT, MET, THI):
    """
    return: dict: {"response": response_sentence, "data": result_dict}
    """
    response = ""
    # 1.先看对应的（材料，方法）下数据库有没有数据
    all_THI = get_all_THI(MET=MET, MAT=MAT)
    # 2.如果没有，走材料推荐
    if len(all_THI) == 0:
        rec_type, new_MAT = material_recommend(MAT)
        response += material_recommend_sentence_with_map.format(MAT=MAT, new_MAT=new_MAT) if rec_type == 'RULE' else material_recommend_sentence_without_map.format(MAT=MAT, new_MAT=new_MAT)
        MAT = new_MAT
    # 3.进行二次查询
    result_dict = paramSQL.select_SQL(MET, MAT, THI)
    # 4.如果没有数据，再走厚度推荐
    if len(result_dict) == 0:
        all_THI = get_all_THI(MET=MET, MAT=MAT)
        THI_left = 0
        THI_right = 0
    # 5. 查询结果解析
    new_result_dict = {}
    for diameter, dataIndexList in result_dict.items():
        # 遍历公共数据表中每组焊丝直径和对应的参数list
        for dataIndex in dataIndexList:
            # 遍历所有参数list
            paramName, paramValue = paramSQL.select_by_ID(dataIndex)[0]
            if diameter not in new_result_dict:
                new_result_dict[diameter] = []
            new_result_dict[diameter].append({paramName: paramValue})
    return {"response": response, "data": new_result_dict}