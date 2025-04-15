import copy

possible_param_values = {
    "Al-Mg-5": ["铝镁5", "铝镁合金", "Al-Mg-5","almg5", "铝镁", "铝镁合金5号", "铝合金Mg-5", "镁铝合金5", "5系铝镁"],
    "Steel": ["不锈钢", "钢材", "steel", "铁", "铁板", "钢", "钢铁", "钢板", "钢筋", "碳钢"] +["优质碳素钢", "奥铁双相钢"],
    "Cu-Si-3": ["铜硅3", "CuSi3", "cusi3", "Cu-Si-3", "铜硅", "铜硅合金3号", "硅铜合金Cu-3", "铜硅合金", "3系铜硅"],
    "Cr-Ni-199": ["铬镍199", "CrNi199", "crni199", "Cr-Ni-199", "铬镍", "铬镍合金199号", "镍铬合金Ni-199", "高铬镍合金", "199系铬镍"],
    "Al-Si-5": ["铝硅5", "AlSi5", "alsi5", "Al-Si-5", "铝硅", "铝硅合金5号", "硅铝合金Si-5", "5系铝硅", "铝硅合金"],
    "Al-99.5": ["纯铝","铝板", "Al995", "al995", "Al-99.5", "铝99.5", "铝管", "铝条", "铝片", "高纯铝", "99.5纯度铝", "工业纯铝", "纯铝板", "铝合金99.5"],
    "MIG": ["CO2", "MAG", "米格", "气保焊", "米格焊", "气体保护焊", "mig", "mig焊接", "二氧化碳气体保护焊"] + ["7保焊", "7宝焊"] + ["mi", "ig"],
    "GMAW": ["熔化极气体保护电弧焊", "格玛", "气体保护焊", "气体电弧焊", "gmaw"],
    "AW": ["ARC", "电弧焊"],
    "TIG": ["氩弧焊", "直流氩弧焊"],
    "FCAW": ["药芯焊丝电弧焊"],
    "FCW-G": ["FCWG", "气保护药芯焊丝电弧焊"],
    "FCW-S": ["FCWS", "自保护药芯焊丝电弧焊"],
    "GMAW-P": ["GMAWP", "熔化极气体保护脉冲电弧焊", "MIG单脉冲", "MIG双脉冲", "单脉冲", "双脉冲"],
    "GMAW-S": ["GMAWS", "熔化极气体保护短路过度电弧焊"],
    "GTAW": ["钨极气体保护电弧焊"],
    "GTAW-P": ["GTAWP", "钨极气体保护脉冲电弧焊"],
    "SMAW": ["焊条电弧焊"]
}

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
        "纯铝": "Al-99.5",
        "铝硅": "Al-Si-5",
        "铝镁": "Al-Mg-5"
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
    "纯铝": ["1090", "1080", "1070", "1060", "1100", "1450"],
    "铝硅": ["4043", "4047", "4A01", "4A11"],
    "铝镁": ["5356", "5183", "5554", "5556", "5A01", "5A02", "5A03"],
    "铝硅镁": ["6A02", "6061", "6063", "6070"]
}
number_values = append_number_values(number_values)
possible_param_values_with_number_values, possible_param_values_without_number_values = append_possible_param_values(possible_param_values, number_values)
possible_param_values = possible_param_values_with_number_values  # 映射到数据库时，还是需要以包含牌号的为准滴
# 构建模糊查询的语料库
param_keys_and_values = {
    'MAT': ['Steel', 'Cu-Si-3', 'Cr-Ni-199', 'Al-Si-5', 'Al-Mg-5', 'Al-99.5'],
    'MET': ['MIG', 'GMAW', "AW", "TIG", "FCAW", "FCW-G", "FCW-S", "GMAW-P", "GMAW-S", "GTAW", "GTAW-P", "SMAW"]
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