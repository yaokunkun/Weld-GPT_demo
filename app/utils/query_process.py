import os.path
import re
from sumeval.metrics.rouge import RougeCalculator

from app.config.config import PROJECT_DIR
from app.utils.materials import corpus_of_value, possible_param_values, number_values
from pycorrector import Corrector
from xpinyin import Pinyin

m=Corrector(
    custom_confusion_path_or_dict=os.path.join(PROJECT_DIR, 'app/utils/my_custom_confusion.txt'),
    custom_word_freq_path=os.path.join(PROJECT_DIR, 'app/utils/custom_word_freq.txt')
)
p = Pinyin()
mapping_chinese_num2arab_num = {'点': '.', '零': '0', '一': '1', '壹': '1', '两':'2', '二': '2', '貳': '2', '三': '3', '叁': '3', '四': '4', '肆': '4', '五': '5', '伍': '4','六': '6', '七': '7', '八': '8', '捌': '8', '九': '9', '玖': '9'}
rouge = RougeCalculator(stopwords=True, lang='zh')
mapping_query_value2standard_value = possible_param_values

# 所有牌号的列表
number_values_list = [item for value_list in number_values.values() for item in value_list]
number_values_list = sorted(number_values_list, key=len, reverse=True)
# 所有焊接方法的列表
key_list = ["MIG", "GMAW", "AW", "TIG", "FCAW", "FCW-G", "FCW-S", "GMAW-P", "GMAW-S", "GTAW", "GTAW-P", "SMAW"]
method_list = [item for key in key_list  for item in possible_param_values[key]]
method_list = sorted(method_list, key=len, reverse=True)
# 所有焊接材料的列表
material_list= corpus_of_value['MAT']
material_list = sorted(material_list, key=len, reverse=True)

def chinese_num2arab_num(query):
    result = ""
    for char in query:
        if char in mapping_chinese_num2arab_num:
            result += mapping_chinese_num2arab_num[char]
        else:
            result += char
    return result

def process_THI(intent, slots):
    """
    ①把单位汉字给抽掉，要让THI对应的值只有数字。
    ②并且，如果捕捉到是厘米查询，则进行单位换算。
    :param intent:
    :param slots:
    :return:
    """
    new_slots = []
    for slot in slots:
        if slot[0] == 'THI':
            thick_with_unit = slot[1]

            re_result = re.findall(r"\d+\.\d+|\d+", thick_with_unit)
            if len(re_result) == 0:
                continue  # 如果说，提取的THI对应的value，居然没有数字，那说明THI提取的有问题，这里必须去掉THI的插槽
            thick = re.findall(r"\d+\.\d+|\d+", thick_with_unit)[0]
            if intent == 'QUERY_CM':
                thick = float(thick)
                thick *= 10
                thick = str(thick)
            new_slot = (slot[0],) + (thick,) + slot[2:]
            new_slots.append(new_slot)
        else:
            new_slots.append(slot)

    return  new_slots

def diff_match(slots, thresholds):
    """
    对NER结果进行模糊匹配
    :param value:
    :param type:
    :param thresholds:一个字典，例如{'MAT': 0.6, 'MET': 0.3}
    :return:
    """
    corpus_of_all = corpus_of_value
    def break_char(value):
        return " ".join(value)

    new_slots = []
    for slot in slots:
        key, value = slot[0], slot[1]
        # 先去除末尾多余的空格
        i = len(value) - 1
        while i >= 0 and value[i] == ' ':
            i -= 1
        value  = value[:i + 1]

        if key in ['THI']:
            new_slots.append((key, value))
            continue
        corpus_of_this_type = corpus_of_all[key]
        if value in corpus_of_this_type:
            # 如果value没有错误，（语料库中有对应的值），直接返回value
            new_slots.append((key, value))
            continue

        value = break_char(value)
        best_match = None
        highest_score = 0.0
        for item in corpus_of_this_type:
            item = break_char(item)
            # 计算当前词与语料库中词的ROUGE-L得分，重点是最长公共子序列
            score  = rouge.rouge_n(
                summary=value,
                references=item,
                n=1)
            if score > highest_score:
                highest_score = score
                best_match = item
        if best_match is not None and highest_score > thresholds[key]:
            best_match = best_match.replace(" ", "")
        else:
            best_match = value.replace(" ", "")
            ## 这个时候进入2°拼音校正
            corrected_value = pinyinconfusion(best_match, corpus_of_this_type)
            if corrected_value:
                print(f"拼音校正成功。{value}->{corrected_value}")
                best_match = corrected_value
        new_slots.append((key, best_match))
    return new_slots

def fix_query(query, slots, fixed_slots):
    """
    传入用户原始的slots和模糊匹配之后的fixed_slots，将query中的可能错误的slot替换为fixed_slot
    :param query:
    :param slots:
    :param fixed_slots:
    :return: fixed_query
    如果数据库中存在这个材料，返回修正后的query，并且查询正常执行；反之，返回错误提醒，以及early_exit信号为True
    """
    for slot, fixed_slot in zip(slots, fixed_slots):
        key = slot[0]
        value = slot[1]
        fixed_value = fixed_slot[1]
        # 逻辑取消
        # # 进行校验，语料库中是否存在该值
        # if key in ['MAT', 'MET'] and fixed_value not in corpus_of_value[key]:
        #     key2name = {'MAT': '焊接材料', 'MET': '焊接方法'}
        #     return f"非常抱歉，您提供的{fixed_value}数据库中并不存在，请您重新提供{key2name[key]}。"
        query = query.replace(value, fixed_value)
    return query

def standardize_value(slots):
    new_slots = []
    for slot in slots:
        key, value = slot[0], slot[1]
        if key in ['THI']:
            new_slots.append((key, value))
            continue
        for standardized, variants in mapping_query_value2standard_value.items():
            if value in variants:
                value = standardized
                break
        new_slots.append((key, value))
    return new_slots

def determine_single_welding_intent(slots):
    """
    根据token_output中识别的实体确定单一的焊接意图。
    实体可能是THI（焊接厚度）、MET（焊接方法）和MAT（焊接材料）。
    函数将返回一个字符串，表示最匹配的查询意图。
    """

    # 标记实体的存在
    has_thi, has_met, has_mat = False, False, False

    # 遍历实体并更新标记
    if isinstance(slots, list):
        for slot in slots:
            if slot[0] == 'THI':
                has_thi = True
            elif slot[0] == 'MET':
                has_met = True
            elif slot[0] == 'MAT':
                has_mat = True
    elif isinstance(slots, dict):
        for key in slots:
            if key == 'THI':
                has_thi = True
            elif key == 'MET':
                has_met = True
            elif key == 'MAT':
                has_mat = True
    else:
        raise TypeError(f"slots must be list or dict, rather than {type(slots)}")

    # 根据实体的组合确定单一的查询意图
    if has_thi and has_met and has_mat:
        return 'QUERY_7'
    elif has_thi and has_met:
        return 'QUERY_4'
    elif has_thi and has_mat:
        return 'QUERY_5'
    elif has_met and has_mat:
        return 'QUERY_6'
    elif has_thi:
        return 'QUERY_1'
    elif has_met:
        return 'QUERY_2'
    elif has_mat:
        return 'QUERY_3'
    else:
        return 'OTHER'

def rule_regconization(query):
    """
    对query进行牌号的材料匹配
    :param query:
    :return:如果匹配到了牌号，返回牌号结果以及擓出牌号和”焊接材料“关键词后的query；如果没有匹配到，则返回None
    """
    # matched_value = None
    matched_result = {}

    def match_MAT(query):
        # First
        matched_value = ""
        for number_value in number_values_list:
            if number_value in query or number_value.lower() in query.lower():
                matched_value = number_value
                break
        lacked_values = {
            "sus": "SUS",
            "su": "SUS",
            "us": "SUS",
            "s": "SUS",
        }
        for lacked_value, complement_value in lacked_values.items():
            if lacked_value.lower() in matched_value.lower():
                matched_value = matched_value.lower()
                matched_value = matched_value.replace(lacked_value.lower(), complement_value)
                break

        # Second
        if matched_value == "":
            for material_value in material_list:
                if material_value in query or material_value.lower() in query.lower():
                    matched_value = material_value
                    break
        return matched_value

    matched_value = match_MAT(query)
    if matched_value != "":
        query = query.replace(matched_value, "")
        MAT_keys = ['焊接材料', '材料', '焊材']
        for MAT_key in MAT_keys:
            query = query.replace(MAT_key, "")
        matched_result['MAT'] = matched_value

    # """
    #    对query进行焊接方法的材料匹配
    #    :param query:
    #    :return:如果匹配到了方法，返回牌号结果以及擓出方法和”焊接方法“关键词后的query；如果没有匹配到，则返回None
    # """
    def match_MET(query):
        matched_value = ""
        for method_value in method_list:
            if method_value in query or method_value.lower() in query.lower():
                matched_value = method_value
                break
        lacked_values = {
            'mi': "mig",
            'ig': "mig",
            'gma': "gma",
            "maw": "gmaw",
            "7保焊": "气保焊",
            "7宝焊": "气保焊",
        }
        if matched_value in lacked_values:
            matched_value = lacked_values[matched_value]
        return matched_value

    matched_value = match_MET(query)
    if matched_value != "":
        # query = query.replace(matched_value, "")
        # MET_keys = ['焊接方法', '焊接方式', '方法', '方式', '用']
        # for MET_key in MET_keys:
        #     query = query.replace(MET_key, "")
        matched_result['MET'] = matched_value

    # """
    #    对query进行焊接厚度的材料匹配
    #    :param query:
    #    :return:如果匹配到了厚度，返回厚度结果以及擓出方法和”焊接方法“关键词后的query；如果没有匹配到，则返回None
    # """
    def match_THI(query):
        matched_value = -1
        # 基于单位进行匹配
        for THI_unit in ["厘米", "毫米", "cm", "mm"]:
            if THI_unit in query:
                unit_index = query.find(THI_unit)
                start_index = unit_index - 1
                while start_index >= 0:
                    if query[start_index].isdigit() or query[start_index] in ['.', '点']:
                        start_index -= 1
                    else:
                        break
                start_index += 1
                if start_index < unit_index:
                    matched_value = query[start_index:unit_index + len(THI_unit)]
                    return matched_value
        # 基于数字进行匹配
        # 情况②：匹配含有小数点的数字，包括小数点前后的数字  (?<![a-zA-Z0-9])(\d+(\.\d+)?)(?![a-zA-Z0-9])
        pattern_case2 = r'\d+\.\d+'
        matches_case2 = re.findall(pattern_case2, query)
        if len(matches_case2) > 0 and len(matches_case2[0]):
            return matches_case2[0]
        # # 情况①：匹配前后没有英文字母和数字的整数
        # pattern_case1 = r'(?<![a-zA-Z0-9])(\d+)(?![a-zA-Z0-9])'
        # matches_case1 = re.findall(pattern_case1, query)
        # if len(matches_case1) > 0 and len(matches_case1[0]) == 1:
        #     return matches_case1[0]
        patterns = [
            r'厚度为(\d+)',
            r'板厚为(\d+)',
            r'厚度是(\d+)',
            r'板厚是(\d+)',
            r'厚度用(\d+)',
            r'板厚用(\d+)',
            r'(\d+)个厚'
        ]
        # 将模式列表连接成一个单一的正则表达式
        combined_pattern = re.compile('|'.join(patterns))
        # 提取每个句子中符合模式的整数
        extracted_numbers = []
        match = combined_pattern.search(query)
        if match:
             for group in match.groups():
                if group:
                    extracted_numbers.append(int(group))
        matched_value = extracted_numbers[0] if len(extracted_numbers) != 0 else -1
        return str(matched_value)

    matched_value = match_THI(query)
    if matched_value != '-1':
        # query = query.replace(matched_value, "")
        # MET_keys = ['焊接厚度', '焊接板厚', '厚度', '板厚', '个厚']
        # for MET_key in MET_keys:
        #     query = query.replace(MET_key, "")
        matched_result['THI'] = matched_value

    return matched_result, query


def update_rule_result(slots, matched_value):
    new_slots = []
    has_MAT = False
    has_MET = False
    has_THI = False
    for slot in slots:
        if slot[0] == 'MAT' and 'MAT' in matched_value:
            new_slots.append(('MAT', matched_value['MAT'], 0, 0))
            has_MAT = True
        elif slot[0] == 'MET' and 'MET' in matched_value:
            new_slots.append(('MET', matched_value['MET'], 0, 0))
            has_MET = True
        elif slot[0] == 'THI' and 'THI' in matched_value:
            new_slots.append(('THI', matched_value['THI'], 0, 0))
            has_THI = True
        else:
            new_slots.append(slot)
    if not has_MAT and 'MAT' in matched_value:
        new_slots.append(('MAT', matched_value['MAT'], 0, 0))
    if not has_MET and 'MET' in matched_value:
        new_slots.append(('MET', matched_value['MET'], 0, 0))
    if not has_THI and 'THI' in matched_value:
        new_slots.append(('THI', matched_value['THI'], 0, 0))
    return new_slots

# def pinyinconfusion(query):
#     corrected_query =  m.correct(query)
#     return corrected_query['target']

def pinyinconfusion(query, corpus_of_this_type):
    def break_char(value):
        return " ".join(value)
    query_pinyin =  p.get_pinyin(query)
    query_pinyin = break_char(query_pinyin)
    best_match = None
    highest_score = 0.0
    for item in corpus_of_this_type:
        item_pinyin = p.get_pinyin(item)
        item_pinyin = break_char(item_pinyin)
        # 计算当前词与语料库中词的ROUGE-L得分，重点是最长公共子序列
        score = rouge.rouge_n(
            summary=query_pinyin,
            references=item_pinyin,
            n=1)
        if score > highest_score:
            highest_score = score
            best_match = item
    if best_match is not None and highest_score > 0.7:
        return best_match.replace(" ", "")
    else:
        return None

def ner_replace(query):
    replace_map = {
        "emi": "mig",
        "柠檬": "40Mn",
        "亚胡汉": "氩弧焊",
        "1胡汉": "氩弧焊",
        "上市": "304",
        "成语": "纯铝",
        "纯女": "纯铝",
        "存李": "纯铝",
        "村民": "纯铝",
        "沿白菊": "mig",
        "7保焊": "气保焊",
        "7宝焊": "气保焊",
        "奥体双相钢": "奥铁双相钢",
        "高铁双相钢": "奥铁双相钢",
        "与美": "铝镁"
    }
    for error_word in replace_map:
        if error_word in query:
            query = query.replace(error_word, replace_map[error_word])
    return query