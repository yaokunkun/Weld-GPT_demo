from app.utils.paramSQL import get_all_MET, get_all_MAT, get_all_THI
from app.utils import paramSQL
from app.utils import userParamSQL

materials_map = {
    '铝18': 'Al-Si-5',
    '铝铁合金': '铝镁合金'
}

material_recommend_sentence_with_map = "您提供的焊接材料是{MAT}，系统推荐您采用{new_MAT}的参数。"
material_recommend_sentence_without_map = "您提供的焊接材料是{MAT}，由于数据库中暂无该材料的数据，根据检索系统建议您采用{new_MAT}的参数。"
thickness_recommend_sentence = "提供的焊接厚度是{THI}，参数由系统推荐计算。"

def rule_recommend(MAT):
    return materials_map[MAT]

def model_recommend(MAT):
    pass

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
        response += material_recommend_sentence_with_map.format(MAT, new_MAT) if rec_type == 'RULE' else material_recommend_sentence_without_map(MAT, new_MAT)
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
    