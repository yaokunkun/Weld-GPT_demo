def state_switch(intent, new_intent):
    # 根据图示创建状态转换表
    transition_table = {
        0: {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7},
        1: {2: 4, 3: 5, 6: 7},
        2: {1: 4, 3: 6, 5: 7},
        3: {1: 5, 2: 6, 4: 7},
        4: {3: 7},
        5: {2: 7},
        6: {1: 7},
        7: {}  # 最终状态
    }

    # 检查是否有此转换
    if new_intent in transition_table[intent]:
        return transition_table[intent][new_intent]
    else:
        return intent  # 如果没有转换，返回原状态
