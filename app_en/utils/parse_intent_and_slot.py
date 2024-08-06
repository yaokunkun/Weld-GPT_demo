from app.utils.paramSQL import select_SQL, get_all_MET, get_all_MAT, get_all_THI


def parse_intent_and_slot(intent, original_slots, standard_slots):
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
        ret = "Okay, I konw welding thickness is {}，please provide welding method and welding material. There are welding methods: {}, and welding materials: {}.".format(THI, all_MET, all_MAT)
        return ret
    elif intent == 'QUERY_2':
        all_THI = get_all_THI(MET=MET)
        ret = "Okay, I konw welding method is {}, please provide welding thickness and welding material. There are welding materials: {}, and welding thicknesses: {}.".format(old_MET, all_MAT, all_THI)
        return ret
    elif intent == 'QUERY_3':
        all_THI = get_all_THI(MAT=MAT)
        ret = "Okay, I konw welding material is {}, please provide welding thickness and welding method. There are welding methods: {}, and welding thicknesses: {}.".format(old_MAT, all_MET, all_THI)
        return ret
    elif intent == 'QUERY_4':
        ret = "Okay, I konw welding thickness is {}, welding method is {}, please provide welding material. There are welding materials: {}.".format(THI, old_MET, all_MAT)
        return ret
    elif intent == 'QUERY_5':
        ret = "Okay, I konw welding thickness is {}, welding material is {}, please provide welding method. There are welding methods: {}.".format(THI, old_MAT, all_MET)
        return ret
    elif intent == 'QUERY_6':
        all_THI = get_all_THI(MET=MET, MAT=MAT)
        # TODO:增加需求：如果这里all_THI是空，则换用其他方法MET查询可选的厚度
        if len(all_THI) == 0:
            for met_candidate in all_MET:
                if met_candidate != MET:
                    all_THI_candidate = get_all_THI(MET=MET, MAT=MAT)
                    if len(all_THI_candidate) != 0:
                        ret = "Okay, the welding method you provide is {}, and welding material is {}, but there is no corresponding welding thickness. You can choose welding method: {}, and then provide welding thickness. In welding method {} you can choose welding thickness: {}".format(old_MET, old_MAT, met_candidate, met_candidate, all_THI_candidate)
                        return  ret
            all_MAT_candidate = []
            for i in all_MAT:
                if i != MAT:
                    all_MAT_candidate.append(i)
            ret = "Sorry, the welding method you provide is {}, and welding material is {}, but there is no corresponding welding thickness. Please choose other welding materials: {}".format(old_MET, old_MAT, all_MAT_candidate)
            return ret
        ret = "Okay, I konw welding method is {}, welding material is {}, please provide welding thickness. There are welding thicknesses: {}.".format(old_MET, old_MAT, all_THI)
        return ret
    elif intent == 'QUERY_7':
        ret = "Okay, I konw welding method is {}, welding material is {}, and welding thickness is {}. Now I'm searching parameters for you.".format(old_MET, old_MAT, THI)
        result_dict = select_SQL(MET, MAT, THI)
        return {"response": ret, "data": result_dict}
    else:
        return "Sorry, I don't konw what you say, please entry again."
