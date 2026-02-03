from app.utils.paramSQL import get_all_MET, get_all_MAT, get_all_THI,select_SQL_rec
from app.utils import paramSQL
from app.utils import userParamSQL
from app.services.bert_param_recommend import recommend,rec_tig_ac,rec_tig_dc

async def parse_intent_and_slot(intent, original_slots, standard_slots, userID):
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

    all_MET = get_all_MET(userID)
    all_MAT = get_all_MAT(userID)
    # 材料为铝返回一个疑问句
    if  MAT.upper()=="AL" and MET.upper()=="MIG" and THI!=0:
        ret= "检测到您查询的焊接方法为 MIG, 焊接材料为铝 , 本系统下铝有多个种类 【\"AlMg \",\"AlSi\",\"pureAl\"】对应参数不同,请输入你想要查询的具体材料"
        return ret
    elif MAT.upper()=="AL" and MET.upper()=="MIG" and THI==0:
        ret = f"检测到您查询的焊接方法为 MIG, 焊接材料为铝 , 本系统下铝有多个种类 【\"AlMg \",\"AlSi\",\"pureAl\"】对应参数不同,请输入你想要查询的具体材料，除此之外请提供焊接厚度"
        return ret
    # 方法在tig大类下进行用户数据库查询
    if MET.upper()in ["TIG","TIG_AC","TIG_DC"]:
        userData_result_dict_tig = paramSQL.select_user_SQL(old_MET, old_MAT, THI, userID)
        user_new_result_dict_tig={}
        #拼接用户库
        if userData_result_dict_tig and len(userData_result_dict_tig) != 0:
            
            for Diameter, ParamName, ParamValue in userData_result_dict_tig :
                DiameterO = f"WireDiameter:{Diameter}"  # 字典键值拼接
                if DiameterO not in user_new_result_dict_tig:
                    user_new_result_dict_tig[DiameterO] = []  # 创建字典键值与对应列表
                user_new_result_dict_tig[DiameterO].append({ParamName: ParamValue})  # 填写列表
        
        # 方法只有TIG
        if MET.upper()=="TIG":
            if MAT.upper()=="AL":
                MET="TIG_AC"
            elif MAT.upper()=="STEEL":
                MET="TIG_DC"
            else:
                ret = f"您查询的TIG焊接方法官方只能使用铝材料或钢材料,铝材使用TIG_AC方法,钢材使用TIG_DC方法,若您真的想要使用TIG方法,请提供焊接材料 或 准确说出焊接方法，同时提供焊接厚度。"
                if len(user_new_result_dict_tig) == 0:
                    return ret
                else:
                    return {"response": ret, "data":"空","data_user": user_new_result_dict_tig}
        # 方法为TIG_AC   
        if  MET.upper()=="TIG_AC" and THI!=0:
            tig_res_dict = rec_tig_ac(THI)
            if len(user_new_result_dict_tig) == 0:
                return tig_res_dict
            else:
                tig_res_dict["data_user"]=user_new_result_dict_tig
                return tig_res_dict
        elif MET.upper()=="TIG_AC" and THI==0:
            ret = f"您查询的TIG_AC焊接方法只能使用铝材料,若想要使用焊机推荐的MIG焊接方法需要使用的焊接材料可以是{all_MAT},若您真的想要使用tig_ac方法,请提供焊接厚度"
            return ret
        # 方法为TIG_DC   
        if  MET.upper()=="TIG_DC" and THI!=0:
            tig_res_dict = rec_tig_dc(THI)
            if len(user_new_result_dict_tig) == 0:
                return tig_res_dict
            else:
                tig_res_dict["data_user"]=user_new_result_dict_tig
                return tig_res_dict
        elif MET.upper()=="TIG_DC" and THI==0:
            ret = f"您查询的TIG_DC焊接方法只能使用钢材料,若想要使用焊机推荐的MIG焊接方法需要使用的焊接材料可以是{all_MAT},若您真的想要使用tig_dc方法,请提供焊接厚度"
            return ret
    
    #焊接方法mig或mma
    if intent == 'QUERY_1':
        all_MET.extend(["TIG_DC","TIG_AC"])
        ret = "好的，我已经知道了焊接厚度是{}，现在请你提供焊接方法和焊接材料。其中焊接方法有：{}，焊接材料有：{}。其中TIG_DC只能用于钢, TIG_AC只能用铝。".format(THI, all_MET, all_MAT)
        return ret
    elif intent == 'QUERY_2':
        all_THI = get_all_THI(userID=userID,MET=MET)
        ret = "好的，我已经知道了焊接方法是{}，现在请你提供焊接材料和焊接厚度。其中焊接材料有：{}，焊接厚度有：{}。".format(old_MET, all_MAT, all_THI)
        return ret
    elif intent == 'QUERY_3':
        all_THI = get_all_THI(userID=userID,MAT=MAT)
        if MAT in ["AlSi","Al","AlMg"]:
            all_MET.append("tig_ac")
        elif MAT=="Steel":
            all_MET.append("tig_dc")
        ret = "好的，我已经知道了焊接材料是{}，现在请你提供焊接方法和焊接厚度。其中焊接方法有：{}，焊接厚度有：{}。".format(old_MAT, all_MET, all_THI)
        return ret
    elif intent == 'QUERY_4':
        ret = "好的，我已经知道了焊接厚度是{}，焊接方法是{}，现在请你提供焊接材料。其中焊接材料有：{}。".format(THI, old_MET, all_MAT)
        return ret
    elif intent == 'QUERY_5':
        if MAT in ["AlSi","Al","AlMg"]:
            all_MET.append("tig_ac")
        elif MAT=="Steel":
            all_MET.append("tig_dc")
        ret = "好的，我已经知道了焊接厚度是{}，焊接材料是{}，现在请你提供焊接方法。其中焊接方法有：{}。".format(THI, old_MAT, all_MET)
        return ret
    elif intent == 'QUERY_6':
        all_THI = get_all_THI(userID=userID,MET=MET, MAT=MAT)
        # TODO:增加需求：如果这里all_THI是空，则换用其他方法MET查询可选的厚度
        if len(all_THI) == 0:
            for met_candidate in all_MET:
                if met_candidate != MET:
                    all_THI_candidate = get_all_THI(userID=userID,MET=MET, MAT=MAT)
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
        ret = "好的，我已经知道了焊接方法是{}，焊接材料是{}，以及焊接厚度是{}。现在我来为您查询参数。我们将展示官方计算和您的自定义参数".format(old_MET, old_MAT, THI)
        #原始查非用户表逻辑
        
        result_dict = paramSQL.select_SQL(MET, MAT, THI)
        THI=float(THI)
        userData_result_dict = paramSQL.select_user_SQL(old_MET, old_MAT, THI, userID)

        print("我们来看看到底为什么不识别：",MET, MAT, THI, userID,result_dict)
        
        
        if len(result_dict) == 0 and len(userData_result_dict) == 0:
            return await recommend(MAT, MET, THI, userID)
        #若官方库需要进行计算厚度我们给他走推荐算法计算一次
        flag=select_SQL_rec(MET,MAT)
        official_cal={}
        if len(flag) != 0 and len(result_dict) == 0 and len(userData_result_dict) != 0:
            official_cal=await recommend(MAT, MET, THI, userID)
            
        print(official_cal)
        new_result_dict = {}
        user_new_result_dict={}
        
        #拼接官方库
        for Diameter, ParamName, ParamValue in result_dict:
            DiameterO=f"WireDiameter:{Diameter}"  #字典键值拼接
            if DiameterO not in new_result_dict:  
                new_result_dict[DiameterO] = []   #创建字典键值与对应列表  产生的数据格式为 {'WireDiameter:10': [ {'焊接方法0': '焊接参数0'}, {'焊接方法1': '焊接参数1'}],'WireDiameter:20': []}
            new_result_dict[DiameterO].append({ParamName: ParamValue})  #填写列表
        
        #拼接用户库
        if userData_result_dict and len(userData_result_dict) != 0:
            
            for Diameter, ParamName, ParamValue in userData_result_dict:
                DiameterO = f"WireDiameter:{Diameter}"  # 字典键值拼接
                if DiameterO not in user_new_result_dict:
                    user_new_result_dict[DiameterO] = []  # 创建字典键值与对应列表
                user_new_result_dict[DiameterO].append({ParamName: ParamValue})  # 填写列表

            if len(result_dict) == 0:
                return {"response": ret, "data": official_cal["data"],"data_user":user_new_result_dict}
            else:
                return {"response": ret, "data": new_result_dict,"data_user":user_new_result_dict}
        else:
            return {"response": ret, "data": new_result_dict,"data_user":"空"}
    else:
        return "不好意思，我没有识别到您提供的参数，请您降低说话语速再次输入。"
