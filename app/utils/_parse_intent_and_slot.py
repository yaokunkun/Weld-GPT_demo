from app.utils.paramSQL import select_SQL, get_all_MET, get_all_MAT, get_all_THI

possible_param_values = {
    "Al-Mg-5": ["铝镁5", "铝镁合金", "Al-Mg-5", "铝镁", "铝镁合金5号", "铝合金Mg-5", "镁铝合金5", "5系铝镁"],
    "Steel": ["不锈钢", "钢材", "Steel", "铁", "碳钢", "铁管", "钢", "钢铁", "铁皮", "铁片", "方管", "镀锌管", "钢板", "钢构件", "结构钢", "建筑用钢", "工业钢材", "钢筋"],
    "Cu-Si-3": ["铜硅3", "CuSi3", "Cu-Si-3", "铜硅", "铜硅合金3号", "硅铜合金Cu-3", "铜硅合金", "3系铜硅"],
    "Cr-Ni-199": ["铬镍199", "CrNi199", "Cr-Ni-199", "铬镍", "铬镍合金199号", "镍铬合金Ni-199", "高铬镍合金", "199系铬镍"],
    "Al-Si-5": ["铝硅5", "AlSi5", "Al-Si-5", "铝硅", "铝硅合金5号", "硅铝合金Si-5", "5系铝硅", "铝硅合金"],
    "Al-99.5": ["纯铝", "Al995", "Al-99.5", "铝99.5", "铝管", "铝条", "铝片", "高纯铝", "99.5纯度铝", "工业纯铝", "纯铝板", "铝合金99.5"],
    "MIG": ["金属惰性气体保护焊", "MIG", "米格", "MIG焊接", "惰性气体金属电弧焊", "米格焊", "金属气体保护焊"],
    "GMAW": ["气体保护金属电弧焊", "GMAW", "格玛", "GMAW焊接", "气体保护焊", "格玛焊接", "气体电弧焊","气保焊"]
}


def parse_intent_and_slot(intent, slots):
    old_MET = ""
    old_MAT = ""
    MET = ""
    MAT = ""
    THI = 0
    DIA = -1  # -1就是没有给焊丝直径
    # （一）从slots中提取参数的值（非标准表述）
    for item in slots:
        key, value = item[0], item[1]
        # （一.5）先去除末尾多余的空格
        i = len(value) - 1
        while i >= 0 and value[i] == ' ':
            i -= 1
        # 切片字符串，去掉末尾的空格部分
        value  = value[:i + 1]
        # （二）利用字典，将MET和MAT从非标准表述，映射为标准表述
        old_value = value
        for standardized, variants in possible_param_values.items():
            if value in variants:
                value = standardized
                break

        if key == 'MET':
            old_MET = old_value
            MET = value
        elif key == 'MAT':
            old_MAT = old_value
            MAT = value
        elif key == 'THI':
            THI = value

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
        ret = "好的，我已经知道了焊接方法是{}，焊接材料是{}，现在请你提供焊接厚度。现在可选的焊接厚度有：{}".format(old_MET, old_MAT, all_THI)
        return ret
    elif intent == 'QUERY_7':
        ret = "好的，我已经知道了焊接方法是{}，焊接材料是{}，以及焊接厚度是{}。现在我来为您查询参数。".format(old_MET, old_MAT, THI)
        result_dict = select_SQL(MET, MAT, THI)
        return {"response": ret, "data": result_dict}
    else:
        return "不好意思，我没有理解您的信息，请您重新输入。"
