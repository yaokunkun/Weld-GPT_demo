
def rule_recommend():
    pass

def model_recommend():
    pass

def material_recommend():
    result = rule_recommend()
    if result:
        return result
    else:
        return model_recommend()
    
def thickness_recommend():
    pass