import logging

from fastapi import APIRouter, Depends
import ast
from app.models.chatbot import ChatRequest, ChatResponse
# from app.services.bert_generation import generation
from app.services.bert_service import predict
from app.utils.parse_intent_and_slot import parse_intent_and_slot
from app.utils.query_process import chinese_num2arab_num, process_THI, diff_match, fix_query, \
    determine_single_welding_intent, standardize_value

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    query = request.query
    logging.info(f"query text: {query}")
    ## ①映射汉字数字到阿拉伯数字
    query = chinese_num2arab_num(query)

    # 调用模型，获取输出
    response = predict(query)
    intent = response['意图']
    slots = response['槽位']
    slots = ast.literal_eval(slots)

    ## ②去除THI中的汉字，并进行单位转换
    slots = process_THI(intent, slots)
    ## ③模糊匹配
    fixed_slots = diff_match(slots, 0.5)

    ### 返回出修正后的query给前端
    fixed_query = fix_query(query, slots, fixed_slots)
    logging.info(f"fixed quert: {fixed_query}")
    ## ③* 查询状态的确定&&状态机的转移
    intent = determine_single_welding_intent(fixed_slots)
    logging.info(f"query state: {intent}")

    ## ④标准化查询值
    standard_slots = standardize_value(fixed_slots)
    # 根据模型输出的意图和实体，整合结果
    response = parse_intent_and_slot(intent, fixed_slots, standard_slots)
    return {"response": response}