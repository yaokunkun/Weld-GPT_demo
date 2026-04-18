import ast
import time
from typing import Dict, Any, List, Tuple
import logging
from fastapi import HTTPException, APIRouter, Body, Request

from app.models.Session import Session
from app.services import session_store
from app.services import bert_service, bert_param_control, bert_intent_recognize
from app.utils.parse_intent_and_slot import parse_intent_and_slot
from app.utils.query_process import chinese_num2arab_num, process_THI, diff_match, fix_query, \
    determine_single_welding_intent, standardize_value, rule_recognition, rule_recognition_user, \
    update_rule_result, ner_replace
from app.utils.state_switch import state_switch
from app.utils import xunfei_translate
from app.api.endpoints import intent_route
from app.api.endpoints.session_en import session_en
import fasttext
import unicodedata

router = APIRouter()
accent_map = {
    '铝镁': ['女美', '旅美'],
    'mig': ['mi狙', 'mi居', 'mi具', 'mag', 'mi区', 'ma区', '掩埋狙', 'ma狙', 'ma居', 'ma具'],
    '铝硅': ['女归'],
    '铝': ['驴'],
}
reversed_map = {}
for key, values in accent_map.items():
    for value in values:
        reversed_map[value] = key

def accent_rule(query):
    for k, v in reversed_map.items():
        if k.lower() in query.lower():
            query = query.lower()
            query = query.replace(k, v)
    return query

#去除标点符号，保留部分标点函数
def remove_punctuation(text: str, keep: str = "-_.") -> str:
    keep_set = set(keep)
    out = []
    for ch in text:
        # Unicode 类别以 P 开头的是标点（Punctuation）
        if unicodedata.category(ch).startswith("P") and ch not in keep_set:
            continue
        out.append(ch)
    return "".join(out)

@router.post("/session/start", response_model=Dict[str, str])
async def start_session(request: Request):
    session = Session()
    redis = getattr(request.app.state, "session_redis", None)
    await session_store.save_session(redis, session, session.id)
    return {"session_id": session.id}


@router.post("/session/{session_id}/", response_model=Dict[str, Any])
async def send_message_query(
    request: Request,
    session_id: str,
    query: str,
    userID: int,
    enable_thinking: bool = False,
):
    
#    start_wall = time.time()
#    start_cpu = time.process_time() 
    
    redis = getattr(request.app.state, "session_redis", None)
    session = await session_store.get_session(redis, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        return await _send_message_query_body(
            query, userID, enable_thinking, session
        )
    finally:
        await session_store.save_session(redis, session, session_id)


async def _send_message_query_body(
    query: str,
    userID: int,
    enable_thinking: bool,
    session: Session,
):
    # 0603: 开头直接检测语言，只要不是中文，直接RAG返回   1119:加入历史记录检测  1124：短文本过滤 1212 去除标点
    query2=remove_punctuation(query)
    session.add_user_messages(query2)
    history_queries=" ".join(session.get_user_messages())
    
    print("历史对话：",history_queries)
    
    language=xunfei_translate.directly_judge_language(query2)    #先用模型判断一下
    if len(query2) < 8 and language!="cn":                       #如果不是中文还短，就判断一下历史记录
        language = xunfei_translate.directly_judge_language(history_queries)
    if language == "un":                                        #如果识别的是un就用网络识别
        language = xunfei_translate.check_language(query2)
        if len(query2) < 8 and language!="cn":                   #如果网络识别不是中文且是短句子那就上历史记录识别，长句子就还是中文走中文，英文走英文
            language = xunfei_translate.check_language(history_queries)
            if language == "un":                                #如果还是识别不出来，那就没招了，直接识别短句query吧。
                language = xunfei_translate.check_language(query2)   
    if language == "en":
        return await session_en(query, session, userID)
    if language not in ["en","cn"]:
        if all(ord(ch) < 128 for ch in query2):
            return await session_en(query, session, userID)
        else:
            return {
                "fixed_query": query,
                # "response": '\n\n'.join([response_text, retrieve_text]),
                "response": f"对不起你输入的语言为{language}，尝试输入英语或中文。\n Sorry, the language you entered is {language}(unsupported), please try entering English or Chinese.",
            }
    
    query = accent_rule(query)
    ## -②.0217需求：把参数查询、电流控制、rag放进一个前端里
    sentence_intent = await bert_intent_recognize.predict(query)
    ### 得到识别的意图∈['RAG', 'CONTROL', 'PARAM']后，根据意图进行不同的处理
    if sentence_intent == "RAG":
        history_messages = session.get_rag_messages()
        # 25.7.4 多返回了推荐问题列表
        response_text, thinking_text, retrieve_text, recommend_list, parsed_media_url= intent_route.get_rag_response(query, history_messages, Enable_thinking=enable_thinking)
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
        response, control_param = await intent_route.get_control_response(query)
        return {
            'fixed_query': fixed_query,
            "response": response,
            'control_param': control_param,
        }
    else:
        print("用户ID",userID)
        ## -①其他语言翻译为中文，防止用户突然切换语言，血的教训！！！！
        ## 检测语言是否是中文
        #language = xunfei_translate.directly_judge_language(query)
        #if language == "un":
        #    language = xunfei_translate.check_language(query)
        ## 不是中文则进行讯飞翻译
        #if language != "cn" and len(query) > 8:
        #    query = xunfei_translate.translate(text=query, source_language=language)
        # 调用模型，获取输出：意图与槽位
        logging.info(f"query text: {query}")
        query = ner_replace(query)
        ## ①映射汉字数字到阿拉伯数字
        query = chinese_num2arab_num(query)
        query = query.replace(" ","")

        ## ①.5基于规则匹配牌号材料
        matched_value_official, query_for_bert = rule_recognition(query, userID)
        matched_value_user = rule_recognition_user(query, userID)

        # 调用模型，获取输出
        response = await bert_service.predict(query_for_bert,userID)
        intent = response['意图']
        slots = response['槽位']
        slots = ast.literal_eval(slots)
        slots_official = update_rule_result(slots, matched_value_official) if matched_value_official != {} else slots
        slots_user = update_rule_result(slots, matched_value_user) if matched_value_user != {} else slots
        logging.info(f"槽位：{slots_user}")
        print(f"槽位：{slots_user}")
        print(f"槽位识别官方：{slots_official}")
        


        ## ②去除THI中的汉字，并进行单位转换
        slots_official = process_THI(intent, slots_official)
        slots_user = process_THI(intent, slots_user)
        # 保留用户原始槽位（用于用户库精确匹配）
        raw_slots = slots_user
        ## ③模糊匹配（仅用于官方库）
        fixed_slots = slots_official if matched_value_official != {} else diff_match(slots_official, {'MAT': 0.7, 'MET': 0.7})  # todo:优化一下


        ### 返回出修正后的query给前端
        # fixed_query, early_exit = fix_query(query, slots, fixed_slots) if not is_instant else query, False
        #### 1°字符修正  2°拼音修正
        fixed_query = query if matched_value_official != {} else fix_query(query, slots_official, fixed_slots)
        logging.info(f"fixed quert: {fixed_query}")


        # session = sessions.get(session_id)
        # if not session:
        #     raise HTTPException(status_code=404, detail="Session not found")

        ## ③* 查询状态的确定
        intent = determine_single_welding_intent(fixed_slots)
        logging.info(f"this chat run's query state: {intent}")

        ## ⑤标准化查询值
        standard_slots = standardize_value(fixed_slots)

        
        
        ## ⑥新session中存储的值（standard value），更新session的状态
        #session.add_and_update(fixed_slots, standard_slots)  2026-01-28 debug
        session.add_and_update(raw_slots, standard_slots)
        new_intent, history_original_slots, history_slots = session.get_intent_and_slots()

        # 根据模型输出的意图和实体，整合结果
        print(fixed_slots)
        response = await parse_intent_and_slot(new_intent, history_original_slots, history_slots, userID)
        

        
        #if isinstance(response, str) and language not in ["cn", "un"]:
        #    response = xunfei_translate.translate_to(text=response, target_language=language)
        #elif language not in ["cn", "un"]:
        #    response["response"] = xunfei_translate.translate_to(text=response["response"], target_language=language)

        session.add_rag_messages(query, response)
        if isinstance(response, dict):
            response["response"] =  (response["response"]) + "\n AI生成仅供参考 " 
        else:
            response =  (response) + "\n AI生成仅供参考 "

    
    #高并发开销计时 
    # end_wall = time.time()
    # end_cpu = time.process_time()
    
    # print("Wall time:", end_wall - start_wall)
    # print("CPU time:", end_cpu - start_cpu)
    
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


# @router.post("/session/{session_id}/response", response_model=Dict[str, Any])
# def send_message_response(session_id: str, fixed_slots = Body(...)):
#     fixed_slots = fixed_slots['slots']
#     session = sessions.get(session_id)
#     if not session:
#         raise HTTPException(status_code=404, detail="Session not found")
    
#     ## ③* 查询状态的确定
#     intent = determine_single_welding_intent(fixed_slots)
#     logging.info(f"query state: {intent}")

#     ## ⑤标准化查询值
#     standard_slots = standardize_value(fixed_slots)

#     ## ⑥新session中存储的值（standard value），更新session的状态
#     session.add_and_update(standard_slots, intent)
#     new_intent, history_slots = session.get_intent_and_slots()

#     # 根据模型输出的意图和实体，整合结果
#     print(fixed_slots)
#     response = parse_intent_and_slot(new_intent, fixed_slots, history_slots)

#     return {"response": response}

# @router.post("/any", response_model=Dict[str, Any])
# def ret_any(input_query, input_str:str):
    return {
        "fixed_query": input_query,
        "response":{
            "response":input_str,
        },
        # "current_slots": [("焊接厚度", "5"), ("焊接方法", "MIG")]
    }
# http://202.38.247.12:8003/api/any?input_query=5个厚，mig&input_str=好的，我已经知道了焊接厚度是5，焊接方法是MIG，现在请你提供焊接材料。

@router.post("/param_query", response_model=Dict[Any, Any])
def param_query(param_dict: dict):
    try:
        MAT = param_dict['MAT']
        MET = param_dict['MET']
        THI = param_dict['THI']
        # DIA = param_dict['DIA']
    except:
        return {
            "response": "参数查询失败，请检查输入的参数格式是否正确。"
        }
    from app.utils.paramSQL import get_param_by_mat_met_thi
    results = get_param_by_mat_met_thi(MAT, MET, THI)
    # results格式：[(Diameter, ParamName, ParamValue), (Diameter, ParamName, ParamValue)]
    if not results or len(results) == 0:
        from app.services.bert_param_recommend import thickness_recommend, material_recommend
        from app.utils.paramSQL import get_all_THI
        all_THI = get_all_THI(MET=MET, MAT=MAT)
        # 1.如果没有，走材料推荐
        if len(all_THI) == 0:
            _, new_MAT = material_recommend(MAT)
            MAT = new_MAT
        # 2.进行二次查询
        results = get_param_by_mat_met_thi(MET, MAT, THI)
        # 4.如果没有数据，再走厚度推荐
        if len(results) == 0:
            recommend_results = thickness_recommend(MAT, MET, THI)
        # recommend_results格式转换到与results一致
        results = []
        for DIA, params_this_DIA in recommend_results.items():
            for ParamName, ParamValue in params_this_DIA.items():
                results.append((DIA, ParamName, ParamValue))

    if results[0][0] == "0":
        ## 没有焊丝直径的参数
        data = [{f"{item[1]}": f"{item[2]}"} for item in results]
        return {
            "response": "查询成功，以下是相关参数信息：",
            "data": data
        }
    else:
        ## 有焊丝直径的参数
        try:
            DIA = param_dict['DIA']
        except:
            return {
                "response": "参数查询失败，请检查输入的参数格式是否正确。"
            }
        results_this_DIA = [item for item in results if str(item[0]) == str(DIA)]
        if not results_this_DIA or len(results_this_DIA) == 0:
            return {
                "response": "根据焊接材料、焊接方法、焊接厚度，已经推荐得到参数值，但该焊丝直径没有对应的值。"
            }
        data = [{f"{item[1]}": f"{item[2]}"} for item in results_this_DIA]
        return {
            "response": "查询成功，以下是相关参数信息：",
            "data": data
        }