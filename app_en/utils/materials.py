import copy

possible_param_values = {
    "Al-Mg-5": ["Aluminum Magnesium 5", "Aluminum Magnesium Alloy", "Al-Mg-5", "almg5", "Aluminum Magnesium", "Aluminum Magnesium Alloy No. 5", "Aluminum Alloy Mg-5", "Magnesium Aluminum Alloy 5", "5 Series Aluminum Magnesium"],
    "Steel": ["Stainless Steel", "Steel Material", "steel", "Iron", "Iron Pipe", "Steel", "Iron and Steel", "Steel Plate", "Rebar", "High-quality Carbon Steel", "Austenitic-ferritic Steel"],
    "Cu-Si-3": ["Copper Silicon 3", "CuSi3", "cusi3", "Cu-Si-3", "Copper Silicon", "Copper Silicon Alloy No. 3", "Silicon Copper Alloy Cu-3", "Copper Silicon Alloy", "3 Series Copper Silicon"],
    "Cr-Ni-199": ["Chromium Nickel 199", "CrNi199", "crni199", "Cr-Ni-199", "Chromium Nickel", "Chromium Nickel Alloy No. 199", "Nickel Chromium Alloy Ni-199", "High Chromium Nickel Alloy", "199 Series Chromium Nickel"],
    "Al-Si-5": ["Aluminum Silicon 5", "AlSi5", "alsi5", "Al-Si-5", "Aluminum Silicon", "Aluminum Silicon Alloy No. 5", "Silicon Aluminum Alloy Si-5", "5 Series Aluminum Silicon", "Aluminum Silicon Alloy"],
    "Al-99.5": ["Pure Aluminum", "Al995", "al995", "Al-99.5", "Aluminum 99.5", "Aluminum Pipe", "Aluminum Bar", "Aluminum Sheet", "High Purity Aluminum", "99.5% Purity Aluminum", "Industrial Pure Aluminum", "Pure Aluminum Plate", "Aluminum Alloy 99.5"],
    "MIG": ["CO2", "MAG", "MIG", "Gas Shielded Welding", "MIG Welding", "Gas Metal Arc Welding", "mig", "CO2 Gas Shielded Welding", "ig", "mi"],
    "GMAW": ["Gas Metal Arc Welding", "GMAW", "Gas Shielded Welding", "Gas Arc Welding", "gmaw"],
    "AW": ["ARC", "Arc Welding"],
    "TIG": ["Tungsten Inert Gas Welding"],
    "FCAW": ["Flux-Cored Arc Welding"],
    "FCW-G": ["FCWG", "Gas Shielded Flux-Cored Arc Welding"],
    "FCW-S": ["FCWS", "Self-Shielded Flux-Cored Arc Welding"],
    "GMAW-P": ["GMAWP", "Pulse Gas Metal Arc Welding", "MIG Single Pulse", "MIG Double Pulse", "Single Pulse", "Double Pulse"],
    "GMAW-S": ["GMAWS", "Short Circuit Transfer Gas Metal Arc Welding"],
    "GTAW": ["Gas Tungsten Arc Welding"],
    "GTAW-P": ["GTAWP", "Pulse Gas Tungsten Arc Welding"],
    "SMAW": ["Shielded Metal Arc Welding"]
}

def append_number_values(number_values):
    for key, value in number_values.items():
        number_value = copy.deepcopy(value)
        if key in ["Ordinary Carbon Steel", "High-quality Carbon Steel", "Shipbuilding Steel", "T Series Tool Steel", "ZG Series Cast Steel"]:
            value += [f"Carbon Steel {i}" for i in number_value]
            if key == "Ordinary Carbon Steel":
                value += [f"Q{i}" for i in number_value]
            elif key == "High-quality Carbon Steel":
                value += [f"{i}Mn" for i in range(15, 76)]
            elif key == "Shipbuilding Steel":
                value += [f"HP{i}" for i in number_value]
            elif key == "T Series Tool Steel":
                value += [f"T{i}" for i in number_value]
            elif key == "ZG Series Cast Steel":
                value += [f"Cast Steel {i}" for i in number_value] + [f"ZG Series Cast Steel {i}" for i in number_value] + ["Cast Steel", "ZG Series Cast Steel"]
                continue
        elif key in ["Austenite", "Ferrite", "Martensite"]:
            value += [f"Stainless Steel {i}" for i in number_value]
            value += [f"{i} Stainless Steel" for i in number_value]
            value += [f"SUS{i}" for i in number_value]
        value += [f"{key} {i}" for i in number_value]
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
        "Pure Aluminum": "Al-99.5",
        "Aluminum Silicon": "Al-Si-5",
        "Aluminum Magnesium": "Al-Mg-5"
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
    "Ordinary Carbon Steel": ["195", "215", "235", "255", "275", "345"],
    "High-quality Carbon Steel": [f"T{i}" for i in range(10, 86)],
    "Shipbuilding Steel": ["245", "265", "295"],
    "T Series Tool Steel": [f"{i}" for i in range(7, 14)],
    "ZG Series Cast Steel": [f"ZG{i}H" for i in range(200, 486)],
    "Austenite": [f"{i}" for i in range(201, 318)],
    "Austenitic Ferritic Duplex Steel": ["SUS329", "2207", "2209"],
    "Ferrite": ["405", "409", "410L", "430", "434", "444"],
    "Martensite": ["403", "410", "420", "440A"],
    "Pure Aluminum": ["1090", "1080", "1070", "1060", "1100", "1450"],
    "Aluminum Silicon": ["4043", "4047", "4A01", "4A11"],
    "Aluminum Magnesium": ["5356", "5183", "5554", "5556", "5A01", "5A02", "5A03"],
    "Aluminum Silicon Magnesium": ["6A02", "6061", "6063", "6070"]
}
number_values = append_number_values(number_values)
possible_param_values_with_number_values, possible_param_values_without_number_values = append_possible_param_values(possible_param_values, number_values)
possible_param_values = possible_param_values_with_number_values  # 映射到数据库时，还是需要以包含牌号的为准滴
# 构建模糊查询的语料库
param_keys_and_values = {
    'MAT': ["Al-Mg-5", "Steel", "Cu-Si-3", "Cr-Ni-199", "Al-Si-5", "Al-99.5"],
    'MET': ["MIG", "GMAW"]
}

corpus_of_value = {
    category: list(set(
        key for sublist in [[k] + possible_param_values_without_number_values[k] for k in keys] for key in sublist
    )) for category, keys in param_keys_and_values.items()
}

# fw = open('/dev_data_2/zkyao/code/Weld-GPT_demo/app/utils/custom_word_freq.txt', 'w+')
# fw = open('/dev_data_2/zkyao/conda/envs/chatchat/lib/python3.8/site-packages/pycorrector/data/person_name.txt', 'w+')
# for key, value in possible_param_values_with_number_values.items():
#     for v in value:
#         fw.write(v + '\t200000' + '\n')
# fw.close()