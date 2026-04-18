
from app.services import bert_intent_recognize_en
from app.api.endpoints import intent_route
##以下都是翻译成中文后用，修改逻辑时去除 
from app.utils import xunfei_translate

from app.utils.query_process import chinese_num2arab_num, process_THI, diff_match, fix_query, \
    determine_single_welding_intent, standardize_value, rule_recognition, update_rule_result, \
    ner_replace
from app.services import bert_service
from app.utils.parse_intent_and_slot import parse_intent_and_slot
import re
import ast
import logging


async def session_en(query, session,userID, enable_thinking = False):
    #测试导入参数类型
    #print(type(session))     #<class 'app.models.Session.Session'>
    #print(session)            #<app.models.Session.Session object at 0x7f5067d9a5e0>
    #print(query,userID)      #My method is MIG, the thickness is 5.5, the material is aluminum magnesium 14
    # 1. 意图识别
    query = query.lower()
    sentence_intent = await bert_intent_recognize_en.predict(query)
    # 2. 根据识别结果分流链路
    if sentence_intent == "RAG":
        history_messages = session.get_rag_messages()
        
        # 25.7.4 多返回了推荐问题列表
        response_text, thinking_text, retrieve_text, recommend_list, parsed_media_url= intent_route.get_rag_response(query, history_messages, language="en", Enable_thinking=enable_thinking)
        session.add_rag_messages(query, response_text)
        return {
            "fixed_query": query,
            # "response": '\n\n'.join([response_text, retrieve_text]),
            "response": response_text,
            "thinking": thinking_text,
            "media_url": parsed_media_url
        }
    elif sentence_intent == "CONTROL":
        fixed_query = query
        response, control_param =await  intent_route.get_control_response(query, language="en")
        return {
            'fixed_query': fixed_query,
            "response": response,
            'control_param': control_param,
        }
        #response, control_param = intent_route.get_control_response(query, language="en")
        # return {
        #     'fixed_query': fixed_query,
        #     "response": "English version control function is under development",
        #     #'control_param': control_param,
        # }
    else:#参数查询逻辑-转换为中文再查询
        print("这是一个数据库查询")
        query = re.sub(r"actig", r"交流氩弧焊", query)
        query = xunfei_translate.translate(text=query, source_language="en")
        query = re.sub(r"米格", r"mig", query)
        query = re.sub(r"阿尔西", r"alsi", query)
        query = re.sub(r"综合格斗", r"mma", query)
        query = re.sub(r"库西", r"cusi", query)
        query = re.sub(r"酷西", r"cusi", query)
        query = re.sub(r"助焊剂", r"flux", query)
        query = re.sub(r"蒂加奇", r"tigac", query)
        query = re.sub(r"阿尔", r"al", query)
        query = re.sub(r"艾尔", r"al", query)
        
        print("成功翻译！")
        # 调用模型，获取输出：意图与槽位
        logging.info(f"query text: {query}")
        query = ner_replace(query)
        ## ①映射汉字数字到阿拉伯数字
        query = chinese_num2arab_num(query)
        query = query.replace(" ","")

        ## ①.5基于规则匹配牌号材料
        matched_value, query_for_bert = rule_recognition(query,userID)

        # 调用模型，获取输出
        response =await bert_service.predict(query_for_bert,userID)
        intent = response['意图']
        slots = response['槽位']
        slots = ast.literal_eval(slots)
        if matched_value != {}:
            slots = update_rule_result(slots, matched_value)
        logging.info(f"槽位：{slots}")
        print(f"槽位：{slots}")

        ## ②去除THI中的汉字，并进行单位转换
        slots = process_THI(intent, slots)
        ## ③模糊匹配
        fixed_slots = slots if matched_value != {} else diff_match(slots, {'MAT': 0.7, 'MET': 0.7})  # todo:优化一下


        ### 返回出修正后的query给前端
        # fixed_query, early_exit = fix_query(query, slots, fixed_slots) if not is_instant else query, False
        #### 1°字符修正  2°拼音修正
        fixed_query = query if matched_value != {} else fix_query(query, slots, fixed_slots)
        logging.info(f"fixed query: {fixed_query}")


        # session = sessions.get(session_id)
        # if not session:
        #     raise HTTPException(status_code=404, detail="Session not found")

        ## ③* 查询状态的确定
        intent = determine_single_welding_intent(fixed_slots)
        logging.info(f"this chat run's query state: {intent}")

        ## ⑤标准化查询值
        standard_slots = standardize_value(fixed_slots)

        ## ⑥新session中存储的值（standard value），更新session的状态
        session.add_and_update(fixed_slots, standard_slots)
        new_intent, history_original_slots, history_slots = session.get_intent_and_slots()

        # 根据模型输出的意图和实体，整合结果
        print(fixed_slots)
        response = await parse_intent_and_slot(new_intent, history_original_slots, history_slots, userID)
        #翻译一下2025-08-29
        #print(type(fixed_query))  #str
        #print(type(response))   ##str和dict都有可能
        fixed_query = xunfei_translate.translate_to(text=fixed_query, target_language='en')
        if isinstance(response, dict):
            response["response"] = xunfei_translate.translate_to(text= response["response"], target_language='en')
        else:
            response=xunfei_translate.translate_to(text= response, target_language='en')
        
        session.add_rag_messages(query, response)
        
        if isinstance(response, dict):
            response["response"] =  (response["response"]) + "\n AI-generated content. Please use with discretion. "
        else:
            response =  (response) +  "\n AI-generated content. Please use with discretion. "


        # 成诺0530新需求：查到数据的时候，多返回一个参数——材料名称
        if 'data' in response and isinstance(response, dict) and len(response['data']) > 0:
            material_name = [standard_slot[1] for standard_slot in standard_slots if standard_slot[0] == 'MAT']
            return{
                "fixed_query": fixed_query,
                "response": response, 
                "current_slots": standard_slots,
                "history_all_slots": history_slots,
                "material_name": material_name
                }
        else:
            return {
                "fixed_query": fixed_query,
                "response": response,
                "current_slots": standard_slots,
                "history_all_slots": history_slots
            }
        # return{
        #     "fixed_query": fixed_query,
        #     "response": "英文版参数识别开发中...",
        #     "current_slots": [],
        #     "material_name": ""
        # }

#if __name__== '__main__':
       