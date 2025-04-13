import ast
from typing import Dict, Any, List, Tuple
import logging
from fastapi import HTTPException, APIRouter, Body

from app.models.Session import Session, sessions
from app.services import bert_service, bert_param_control, bert_intent_recognize
from app.utils.parse_intent_and_slot import parse_intent_and_slot
from app.utils.query_process import chinese_num2arab_num, process_THI, diff_match, fix_query, \
    determine_single_welding_intent, standardize_value, rule_regconization, update_rule_result, \
    ner_replace
from app.utils.state_switch import state_switch
from app.utils import xunfei_translate
from app.api.endpoints import intent_route

import fasttext

router = APIRouter()


@router.post("/session/start", response_model=Dict[str, str])
def start_session():
    session = Session()
    sessions[session.id] = session
    return {"session_id": session.id}


@router.post("/session/{session_id}/", response_model=Dict[str, Any])
def send_message_query(session_id: str, query: str, userID: int):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    ## -②.0217需求：把参数查询、电流控制、rag放进一个前端里
    sentence_intent = bert_intent_recognize.predict(query)
    if sentence_intent == "RAG":
        fixed_query = query
        response = intent_route.get_rag_response(query)
        return {
            "fixed_query": fixed_query,
            "response": response,
        }
    elif sentence_intent == "CONTROL":
        fixed_query = query
        response, control_param = intent_route.get_control_response(query)
        return {
            'fixed_query': fixed_query,
            "response": response,
            'control_param': control_param,
        }
    else:
        # -①其他语言翻译为中文
        ## 检测语言是否是中文
        language = xunfei_translate.directly_judge_language(query)
        if language == "un":
            language = xunfei_translate.check_language(query)
        ## 不是中文则进行讯飞翻译
        if language != "cn" and len(query) > 8:
            query = xunfei_translate.translate(text=query, source_language=language)
        # 调用模型，获取输出：意图与槽位
        logging.info(f"query text: {query}")
        query = ner_replace(query)
        ## ①映射汉字数字到阿拉伯数字
        query = chinese_num2arab_num(query)
        query = query.replace(" ","")

        ## ①.5基于规则匹配牌号材料
        matched_value, query_for_bert = rule_regconization(query)

        # 调用模型，获取输出
        response = bert_service.predict(query_for_bert)
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
        logging.info(f"fixed quert: {fixed_query}")


        session = sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

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
        response = parse_intent_and_slot(new_intent, history_original_slots, history_slots, userID)
        if isinstance(response, str) and language not in ["cn", "un"]:
            response = xunfei_translate.translate_to(text=response, target_language=language)
        elif language not in ["cn", "un"]:
            response["response"] = xunfei_translate.translate_to(text=response["response"], target_language=language)
    return {
        "fixed_query": fixed_query,
        "response": response,
        "current_slots": standard_slots
    }


@router.post("/session/{session_id}/response", response_model=Dict[str, Any])
def send_message_response(session_id: str, fixed_slots = Body(...)):
    fixed_slots = fixed_slots['slots']
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    ## ③* 查询状态的确定
    intent = determine_single_welding_intent(fixed_slots)
    logging.info(f"query state: {intent}")

    ## ⑤标准化查询值
    standard_slots = standardize_value(fixed_slots)

    ## ⑥新session中存储的值（standard value），更新session的状态
    session.add_and_update(standard_slots, intent)
    new_intent, history_slots = session.get_intent_and_slots()

    # 根据模型输出的意图和实体，整合结果
    print(fixed_slots)
    response = parse_intent_and_slot(new_intent, fixed_slots, history_slots)

    return {"response": response}

@router.post("/any", response_model=Dict[str, Any])
def ret_any(input_query, input_str:str):
    return {
        "fixed_query": input_query,
        "response":{
            "response":input_str,
        },
        # "current_slots": [("焊接厚度", "5"), ("焊接方法", "MIG")]
    }
# http://202.38.247.12:8003/api/any?input_query=5个厚，mig&input_str=好的，我已经知道了焊接厚度是5，焊接方法是MIG，现在请你提供焊接材料。