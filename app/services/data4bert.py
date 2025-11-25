import json
import random
from collections import Counter

# 可选的参数值
welding_methods = ['MIG', 'GMAW']
welding_materials = ['Steel', 'Cu-Si-3', 'Cr-Ni-199', 'Al-Si-5', 'Al-Mg-5', 'Al-99.5']
thickness_values = ['0.6', '0.8', '1', '1.5', '2']

weld_args = {'THI': ['焊接厚度', thickness_values],
             'MAT': ['焊接材料', welding_materials],
             'MET': ['焊接方法', welding_methods]}

# 口语词汇替换选项
initial_words = ["我现在了解到", "我刚查到", "我明白了", "我刚发现", "我了解了", "我查证后发现", "我研究过后得知",
                 "我已掌握到", "我看到了", "我得知的信息是", "我刚刚确认", "我注意到了", "我了解的情况是"]
additional_words = ["另外", "此外", "除此之外", "同时", "而且", "加之", "再者", "再加上", "又有", "以及"]
closing_words = ["请告诉我需要哪些参数", "我需要知道哪些参数", "能告诉我需要哪些参数吗", "请列出我需要的参数",
                 "哪些参数是必须的", "能列举需要的参数吗", "请问要哪些参数", "请详细告诉我需要的参数",
                 "你能指明所需参数吗", "请说明需要的参数"]

# 关键词变化
key_variations = {
    "焊接方法": ["方法", "焊接方式"],
    "焊接材料": ["材料", "焊材"],
    "焊接厚度": ["厚度", "焊接的厚度"]
}

# 噪声词
noise_words = ["嗯", "呐", "啊", "哦", "额", "哈", "诶"]

possible_param_values = {
    "Al-Mg-5": ["铝镁5", "铝镁合金", "Al-Mg-5"],
    "Steel": ["不锈钢", "钢材", "Steel"],
    "Cu-Si-3": ["铜硅3", "CuSi3", "Cu-Si-3"],
    "Cr-Ni-199": ["铬镍199", "CrNi199", "Cr-Ni-199"],
    "Al-Si-5": ["铝硅5", "AlSi5", "Al-Si-5"],
    "Al-99.5": ["纯铝", "Al995", "Al-99.5"],
    "MIG": ["金属惰性气体保护焊", "MIG", "米格"],
    "GMAW": ["气体保护金属电弧焊", "GMAW", "格玛"]
}

# 意图类型
# QUERY_1   查询材料厚度
# QUERY_2   查询焊接方法
# QUERY_3   查询焊接材料
# QUERY_4   查询材料厚度和焊接方法
# QUERY_5   查询材料厚度和焊接材料
# QUERY_6   查询焊接方法和焊接材料
# QUERY_7   查询材料厚度和焊接方法和焊接材料
# OTHER       其他
intents = ['OTHER', 'QUERY_1', 'QUERY_2', 'QUERY_3', 'QUERY_4', 'QUERY_5', 'QUERY_6', 'QUERY_7']


def get_sub_q(arg_label, arg_value):
    if arg_label == 'THI':
        return f"{key_variations['焊接厚度'][random.randint(0, len(key_variations['焊接厚度']) - 1)]}" \
               f"是{arg_value}", arg_value
    elif arg_label == 'MAT':
        temp_arg_value = random.choice(possible_param_values.get(arg_value, [arg_value]))
        return f"{key_variations['焊接材料'][random.randint(0, len(key_variations['焊接材料']) - 1)]}" \
               f"是{temp_arg_value}", temp_arg_value
    elif arg_label == 'MET':
        temp_arg_value = random.choice(possible_param_values.get(arg_value, [arg_value]))
        return f"{key_variations['焊接方法'][random.randint(0, len(key_variations['焊接方法']) - 1)]}" \
               f"是{temp_arg_value}", temp_arg_value


def gen_3_cond(arg_label1, arg_label2, arg_label3):
    """ 用3个条件生成 """
    generated_data = []
    num_epochs = 40
    # 遍历所有可能的组合
    for epoch in range(num_epochs):
        for arg_value1 in weld_args[arg_label1][1]:
            for arg_value2 in weld_args[arg_label2][1]:
                for arg_value3 in weld_args[arg_label3][1]:
                    # 随机选择口语词汇进行替换
                    sub1, temp_arg_value1 = get_sub_q(arg_label1, arg_value1)  # 条件 1
                    sub2, temp_arg_value2 = get_sub_q(arg_label2, arg_value2)  # 条件 2
                    sub3, temp_arg_value3 = get_sub_q(arg_label3, arg_value3)  # 条件 3

                    sub_questions = [sub1, sub2, sub3]
                    random.shuffle(sub_questions)  # 打乱三个条件

                    question = f"{random.choice(initial_words)}" \
                               f"{sub_questions[0]}，" \
                               f"{random.choice(noise_words)}，{random.choice(additional_words)}" \
                               f"{sub_questions[1]}，" \
                               f"{random.choice(noise_words)}，{random.choice(additional_words)}" \
                               f"{sub_questions[2]}，" \
                               f"{random.choice(closing_words)}。"

                    # 存储到列表
                    generated_data.append({
                        'text': question,
                        'domain': 'weld',
                        'intent': 'QUERY_7',
                        'slots': {arg_label1: temp_arg_value1,
                                  arg_label2: temp_arg_value2,
                                  arg_label3: temp_arg_value3}
                    })

    return generated_data


def gen_2_cond(arg_label1, arg_label2):
    """ 用2个条件生成 """
    generated_data = []
    num_epochs = 40
    # 遍历所有可能的组合
    for epoch in range(num_epochs):
        for arg_value1 in weld_args[arg_label1][1]:
            for arg_value2 in weld_args[arg_label2][1]:
                # 随机选择口语词汇进行替换
                sub1, temp_arg_value1 = get_sub_q(arg_label1, arg_value1)  # 条件 1
                sub2, temp_arg_value2 = get_sub_q(arg_label2, arg_value2)  # 条件 2
                sub_questions = [sub1, sub2]
                random.shuffle(sub_questions)  # 打乱2个条件
                question = f"{random.choice(initial_words)}" \
                           f"{sub_questions[0]}，" \
                           f"{random.choice(noise_words)}，{random.choice(additional_words)}" \
                           f"{sub_questions[1]}，" \
                           f"{random.choice(closing_words)}。"

                intent_label = ''
                if Counter([arg_label1, arg_label2]) == Counter(['THI', 'MET']):
                    intent_label = 'QUERY_4'
                elif Counter([arg_label1, arg_label2]) == Counter(['THI', 'MAT']):
                    intent_label = 'QUERY_5'
                elif Counter([arg_label1, arg_label2]) == Counter(['MAT', 'MET']):
                    intent_label = 'QUERY_6'

                # 存储到列表
                generated_data.append({
                    'text': question,
                    'domain': 'weld',
                    'intent': intent_label,
                    'slots': {arg_label1: temp_arg_value1,
                              arg_label2: temp_arg_value2}
                })

    return generated_data


def gen_1_cond(arg_label1):
    """ 用1个条件生成 """
    generated_data = []
    num_epochs = 40
    # 遍历所有可能的组合
    for epoch in range(num_epochs):
        for arg_value1 in weld_args[arg_label1][1]:
            # 随机选择口语词汇进行替换
            sub1, temp_arg_value1 = get_sub_q(arg_label1, arg_value1)  # 条件 1
            question = f"{random.choice(initial_words)}" \
                       f"{sub1}，" \
                       f"{random.choice(noise_words)}，" \
                       f"{random.choice(closing_words)}。"

            intent_label = ''
            if arg_label1 == 'THI':
                intent_label = 'QUERY_1'
            elif arg_label1 == 'MET':
                intent_label = 'QUERY_2'
            elif arg_label1 == 'MAT':
                intent_label = 'QUERY_3'

            # 存储到列表
            generated_data.append({
                'text': question,
                'domain': 'weld',
                'intent': intent_label,
                'slots': {arg_label1: temp_arg_value1}
            })

    return generated_data


def gen_other():
    generated_data = []

    texts = ['你是谁啊',
             '你在干嘛',
             '我不高兴了',
             '这是在做什么',
             '我不告诉你',
             '今天天气不错啊']

    for text in texts:
        generated_data.append({
            'text': text,
            'domain': 'weld',
            'intent': 'OTHER',
            'slots': {}
        })

    return generated_data


# 存储生成的数据
total_data = gen_3_cond('THI', 'MAT', 'MET') \
             + gen_2_cond('THI', 'MAT') + gen_2_cond('THI', 'MET') + gen_2_cond('MET', 'MAT') \
             + gen_1_cond('THI') + gen_1_cond('MAT') + gen_1_cond('MET') \
             + gen_other()

random.shuffle(total_data)

total_num = len(total_data)
train_data = total_data[:int(total_num * 0.9)]
temp_test_data = total_data[int(total_num * 0.9):]

test_data = [{'text': x['text']} for x in temp_test_data]

# 保存为JSON文件
with open('train.json', 'w', encoding='utf-8') as f:
    json.dump(train_data, f, ensure_ascii=False, indent=4)

with open('test.json', 'w', encoding='utf-8') as f:
    json.dump(test_data, f, ensure_ascii=False, indent=4)
