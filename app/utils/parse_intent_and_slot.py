from app.utils.paramSQL import get_all_MET, get_all_MAT, get_all_THI
from app.utils import paramSQL
from app.utils import userParamSQL

def parse_intent_and_slot(intent, original_slots, standard_slots, userID):
    """
    用处理好的NER，查询数据库，并得到response
    :param intent:
    :param original_slots: 用户口头表述的参数value（经过模糊查询校正过的）
    :param standard_slots: 数据库中存储的标准参数value
    :return: response
    """
    old_MET = ""
    old_MAT = ""
    MET = ""
    MAT = ""
    THI = 0
    for standard_slot in standard_slots:
        if standard_slot[0] == 'MET':
            old_MET = standard_slot[1]
            MET = standard_slot[1]
        elif standard_slot[0] == 'MAT':
            old_MAT = standard_slot[1]
            MAT = standard_slot[1]
        elif standard_slot[0] == 'THI':
            THI = standard_slot[1]

    for fixed_slot in original_slots:
        if fixed_slot[0] == 'MET':
            old_MET = fixed_slot[1]
        elif fixed_slot[0] == 'MAT':
            old_MAT = fixed_slot[1]

    all_MET = get_all_MET()
    all_MAT = get_all_MAT()
    if intent == 'QUERY_1':
        ret = "好的，我已经知道了焊接厚度是{}，现在请你提供焊接方法和焊接材料。其中焊接方法有：{}，焊接材料有：{}。".format(THI, all_MET, all_MAT)
        return ret
    elif intent == 'QUERY_2':
        all_THI = get_all_THI(MET=MET)
        ret = "好的，我已经知道了焊接方法是{}，现在请你提供焊接材料和焊接厚度。其中焊接材料有：{}，焊接厚度有：{}。".format(old_MET, all_MAT, all_THI)
        return ret
    elif intent == 'QUERY_3':
        all_THI = get_all_THI(MAT=MAT)
        ret = "好的，我已经知道了焊接材料是{}，现在请你提供焊接方法和焊接厚度。其中焊接方法有：{}，焊接厚度有：{}。".format(old_MAT, all_MET, all_THI)
        return ret
    elif intent == 'QUERY_4':
        ret = "好的，我已经知道了焊接厚度是{}，焊接方法是{}，现在请你提供焊接材料。其中焊接材料有：{}。".format(THI, old_MET, all_MAT)
        return ret
    elif intent == 'QUERY_5':
        ret = "好的，我已经知道了焊接厚度是{}，焊接材料是{}，现在请你提供焊接方法。其中焊接方法有：{}。".format(THI, old_MAT, all_MET)
        return ret
    elif intent == 'QUERY_6':
        all_THI = get_all_THI(MET=MET, MAT=MAT)
        # TODO:增加需求：如果这里all_THI是空，则换用其他方法MET查询可选的厚度
        if len(all_THI) == 0:
            for met_candidate in all_MET:
                if met_candidate != MET:
                    all_THI_candidate = get_all_THI(MET=MET, MAT=MAT)
                    if len(all_THI_candidate) != 0:
                        ret = "好的，你提供的焊接方法是{}，焊接材料是{}，但是没有对应的焊接厚度。你可以选择焊接方法{}，然后提供焊接厚度。焊接方法{}可选的焊接厚度有：{}".format(old_MET, old_MAT, met_candidate, met_candidate, all_THI_candidate)
                        return  ret
            all_MAT_candidate = []
            for i in all_MAT:
                if i != MAT:
                    all_MAT_candidate.append(i)
            ret = "不好意思，你提供的焊接方法是{}，焊接材料是{}，目前没有对应的焊接厚度，请更换为其他焊接材料：{}".format(old_MET, old_MAT, all_MAT_candidate)
            return ret
        ret = "好的，我已经知道了焊接方法是{}，焊接材料是{}，现在请你提供焊接厚度。现在可选的焊接厚度有：{}".format(old_MET, old_MAT, all_THI)
        return ret
    elif intent == 'QUERY_7':
        ret = "好的，我已经知道了焊接方法是{}，焊接材料是{}，以及焊接厚度是{}。现在我来为您查询参数。".format(old_MET, old_MAT, THI)
        result_dict = paramSQL.select_SQL(MET, MAT, THI)
        userData_result_dict = userParamSQL.select_SQL(MET, MAT, THI, userID)
        new_result_dict = {}
        for diameter, dataIndexList in result_dict.items():
            # 遍历公共数据表中每组焊丝直径和对应的参数list
            for dataIndex in dataIndexList:
                # 遍历所有参数list
                paramName, paramValue = paramSQL.select_by_ID(dataIndex)[0]
                if diameter not in new_result_dict:
                    new_result_dict[diameter] = []
                new_result_dict[diameter].append({paramName: paramValue})

        for diameter, dataIndexList in userData_result_dict.items():
            # 遍历用户个人数据表中每组焊丝直径和对应的参数list
            for dataIndex in dataIndexList:
                # 遍历所有参数list
                paramName, _ = paramSQL.select_by_ID(dataIndex)[0]
                paramValue = userParamSQL.select_by_ID(dataIndex, userID)[0]
                if diameter not in new_result_dict:
                    new_result_dict[diameter] = []
                new_result_dict[diameter].append({paramName: paramValue})

        return {"response": ret, "data": new_result_dict}
    else:
        return "不好意思，我没有识别到您提供的参数，请您降低说话语速再次输入。"
