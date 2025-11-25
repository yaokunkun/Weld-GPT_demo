import copy

possible_param_values = {
    "AlMg": ["铝镁5", "铝镁合金", "AL-MG-5","almg5", "铝镁", "铝镁合金5号", "铝合金MG-5", "镁铝合金5", "5系铝镁","镁铝"],
    "Steel": ["不锈钢", "钢材", "steel", "钢", "钢铁", "钢板", "钢筋", "碳钢"] +["优质碳素钢", "奥铁双相钢"],
    "Fe":["铁", "铁板"],
    "CuSi": ["铜硅3", "CUSI3", "cusi3", "CU-SI-3", "铜硅", "铜硅合金3号", "硅铜合金Cu-3", "铜硅合金", "3系铜硅","硅铜"],
    "药芯":["药芯","管状焊丝","粉芯焊丝","flux-Cored","tubular","要新","药心","管状"],
    "AlSi": ["铝硅5","al-si", "ALSI5", "alsi5", "al-si-5", "铝硅", "铝硅合金5号", "硅铝合金Si-5", "5系铝硅", "铝硅合金","铝硅4","al-si-4","硅铝"]+["纯粹","纯铝","AL995", "al995", "AL-99.5", "铝99.5", "高纯铝", "99.5纯度铝", "工业纯铝", "纯铝板", "铝合金99.5","PUREAL","PURE ALUMINUM"],
    #"pureAl": ["纯铝","铝板", "AL995", "al995", "AL-99.5", "铝99.5", "铝管", "铝条", "铝片", "高纯铝", "99.5纯度铝", "工业纯铝", "纯铝板", "铝合金99.5","ALUMINUM","铝"],
    "Al": ["铝板", "铝管", "铝条", "铝片", "ALUMINUM","铝"],
    "MIG": ["CO2", "MAG", "米格", "气保焊", "米格焊", "气体保护焊", "mig", "mig焊接", "二氧化碳气体保护焊", "氩弧焊"] + ["7保焊", "7宝焊"] + ["mi", "ig"],
    #"GTAW": ["钨极气体保护电弧焊","GTAWP", "钨极气体保护脉冲电弧焊","GMAWS", "熔化极气体保护短路过度电弧焊","GMAWP", "熔化极气体保护脉冲电弧焊", "MIG单脉冲", "MIG双脉冲", "单脉冲", "双脉冲","熔化极气体保护电弧焊", "格玛", "气体保护焊", "气体电弧焊", "gmaw"],
    #"SMAW": ["焊条电弧焊"]
    "MMA": ["MMA","手工电弧焊","焊条电弧焊","SMAW","stick welding","手工金属电弧焊","药皮焊条电弧焊", "涂药焊条电弧焊","电焊","手把焊","条焊","棒焊","手工焊","传统电弧焊","焊条焊","电弧手工焊","药芯焊条焊","工地焊"],
    "TIG_AC": [ "TIG_AC","交流TIG","TIG交流","ACTIG","AC-TIG","TIGAC","TIG-AC","GTAWAC","GTAW-AC","交流钨极惰性气体保护焊","交流钨极氩弧焊","交流氩弧焊","铝TIG焊","TIG铝焊","交流GTAW","钨极交流氩弧焊","交流手工钨极氩弧焊","AC-GTAW","ACGTAW","tig welding with ac","alternating current tig","交流非熔化极惰性气体保护焊","交流非熔化极氩弧焊","手工交流TIG焊","铝材专用TIG焊"],
    "TIG_DC": [ "TIG_DC","直流TIG","TIG直流","DCTIG","DC-TIG","TIGDC","TIG-DC","GTAWDC","GTAW-DC","直流钨极惰性气体保护焊","直流钨极氩弧焊","直流氩弧焊","钢TIG焊","TIG钢焊","直流GTAW","钨极直流氩弧焊","直流手工钨极氩弧焊","DC-GTAW","DCGTAW","tig welding with dc","direct current tig","直流非熔化极惰性气体保护焊","直流非熔化极氩弧焊","手工直流TIG焊","钢材专用TIG焊"],
}
    # "Al-Mg-5": ["铝镁5", "铝镁合金", "Al-Mg-5","almg5", "铝镁", "铝镁合金5号", "铝合金Mg-5", "镁铝合金5", "5系铝镁"],
    # "Steel": ["不锈钢", "钢材", "steel", "铁", "铁板", "钢", "钢铁", "钢板", "钢筋", "碳钢"] +["优质碳素钢", "奥铁双相钢"],
    # "Cu-Si-3": ["铜硅3", "CuSi3", "cusi3", "Cu-Si-3", "铜硅", "铜硅合金3号", "硅铜合金Cu-3", "铜硅合金", "3系铜硅"],
    # "Cr-Ni-199": ["铬镍199", "CrNi199", "crni199", "Cr-Ni-199", "铬镍", "铬镍合金199号", "镍铬合金Ni-199", "高铬镍合金", "199系铬镍"],
    # "Al-Si-5": ["铝硅5", "AlSi5", "alsi5", "Al-Si-5", "铝硅", "铝硅合金5号", "硅铝合金Si-5", "5系铝硅", "铝硅合金"],
    # "Al-Si-4": ["铝硅4"],
    # "Al-99.5": ["纯铝","铝板", "Al995", "al995", "Al-99.5", "铝99.5", "铝管", "铝条", "铝片", "高纯铝", "99.5纯度铝", "工业纯铝", "纯铝板", "铝合金99.5"],
    # "MIG": ["CO2", "MAG", "米格", "气保焊", "米格焊", "气体保护焊", "mig", "mig焊接", "二氧化碳气体保护焊", "氩弧焊"] + ["7保焊", "7宝焊"] + ["mi", "ig"],
    # "GMAW": ["熔化极气体保护电弧焊", "格玛", "气体保护焊", "气体电弧焊", "gmaw"],
    # "AW": ["ARC", "电弧焊"],
    # "TIG": ["直流氩弧焊"],
    # "FCAW": ["药芯焊丝电弧焊"],
    # "FCW-G": ["FCWG", "气保护药芯焊丝电弧焊"],
    # "FCW-S": ["FCWS", "自保护药芯焊丝电弧焊"],
    # "GMAW-P": ["GMAWP", "熔化极气体保护脉冲电弧焊", "MIG单脉冲", "MIG双脉冲", "单脉冲", "双脉冲"],
    # "GMAW-S": ["GMAWS", "熔化极气体保护短路过度电弧焊"],
    # "GTAW": ["钨极气体保护电弧焊"],
    # "GTAW-P": ["GTAWP", "钨极气体保护脉冲电弧焊"],
    # "SMAW": ["焊条电弧焊"]

def append_number_values(number_values):
    for key, value in number_values.items():
        number_value = copy.deepcopy(value)
        if key in ["普通碳钢", "优质碳素钢", "船用钢", "T系列工具钢", "ZG系列铸造钢"]:
            value += [f"碳钢{i}" for i in number_value]
            if key == "普通碳钢":
                value += [f"Q{i}" for i in number_value]
            elif key == "优质碳素钢":
                value += [f"{i}Mn" for i in range(15, 76)]
            elif key == "船用钢":
                value += [f"HP{i}" for i in number_value]
            elif key == "T系列工具钢":
                # value += [f"T{i}" for i in number_value]
                continue
            elif key == "ZG系列铸造钢":
                value += [f"铸造钢{i}" for i in number_value] + [f"ZG系列铸造钢{i}" for i in number_value] + ["铸造钢", "ZG系列铸造钢"]
                continue
        elif key in ["奥氏体", "铁素体", "马氏体"]:
            value += [f"不锈钢{i}" for i in number_value]
            value += [f"{i}不锈钢" for i in number_value]
            value += [f"S{i}" for i in number_value]
            value += [f"SUS{i}" for i in number_value]
        value += [f"{key}{i}" for i in number_value]
        value += [f"{key}"]
    return number_values

def append_possible_param_values(possible_param_values, number_values):
    """
    根据牌号数据的字典，添加进possible_param_values中。返回包含牌号的
    possible_param_values_with_number_values，和专门去掉牌号的（用于训练数据构造和防止牌号干扰模糊查询）
    possible_param_values_without_number_values
    :param possible_param_values: 非牌号的查询参数值表达方式
    :param number_values: 牌号数据
    :return: possible_param_values_with_number_values, possible_param_values_without_number_values
    """
    number_values = copy.deepcopy(number_values)
    possible_param_values_with_number_values = copy.deepcopy(possible_param_values)
    possible_param_values_without_number_values = copy.deepcopy(possible_param_values)
    key_mapping = {
       # "纯铝": "Al",
        "铝硅": "AlSi",
        "铝镁": "AlMg"
    }
    # 遍历映射字典，更新possible_param_values并从number_values中移除已处理的键
    for original_key, new_key in key_mapping.items():
        if original_key in number_values:
            possible_param_values_with_number_values[new_key] += number_values.pop(original_key)
    # 将剩余的number_values添加到possible_param_values
    possible_param_values_with_number_values.update(number_values)
    # 专门再创建去掉牌号的字典possible_param_values_without_number_values
    for key, value in number_values.items():
        possible_param_values_without_number_values[key] = [key]

    return possible_param_values_with_number_values, possible_param_values_without_number_values

number_values = {
    "普通碳钢": ["195", "215", "235", "255", "275", "345"],
    "优质碳素钢": [f"T{i}" for i in range(10, 86)],
    "船用钢": ["245", "265", "295"],
    "T系列工具钢": [f"T{i}" for i in range(7, 14)],
    "ZG系列铸造钢": [f"ZG{i}H" for i in range(200, 486)],
    "奥氏体": [f"{i}" for i in range(201, 318)],
    "奥铁双相钢": ["329", "2207", "2209","S329", "S2207", "S2209", "SUS329", "SUS2207", "SUS2209"],
    "铁素体": ["405", "409", "410L", "430", "434", "444"],
    "马氏体": ["403", "410", "420", "440A"],
    "纯铝1090": ["1090", "1080", "1070", "1060", "1100", "1450"],
    "铝硅4043": ["4043", "4047", "4A01", "4A11"],
    "铝镁5356": ["5356", "5183", "5554", "5556", "5A01", "5A02", "5A03"],
    "铝硅镁6A02": ["6A02", "6061", "6063", "6070"]
}
number_values = append_number_values(number_values)
possible_param_values_with_number_values, possible_param_values_without_number_values = append_possible_param_values(possible_param_values, number_values)
possible_param_values = possible_param_values_with_number_values  # 映射到数据库时，还是需要以包含牌号的为准滴
# 构建模糊查询的语料库
param_keys_and_values = {
    'MAT': ["AlMg","Steel","Fe","CuSi","药芯","AlSi","Al"],
    'MET': ["MIG","TIG_DC","MMA","TIG_AC"]
}

corpus_of_value = {
    category: list(set(
        key for sublist in [[k] + possible_param_values_without_number_values[k] for k in keys] for key in sublist
    )) for category, keys in param_keys_and_values.items()
}


if __name__ == "__main__":
    number_values_list = sum([value for value in number_values.values()], [])
    print(number_values_list)
    print("==================")
    corpus_of_value_list =  sum([value for value in corpus_of_value.values()], [])
    print(corpus_of_value_list)