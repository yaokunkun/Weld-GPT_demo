from fastapi import FastAPI
from contextlib import asynccontextmanager
from pydantic import BaseModel
from app.config import config
import torch
import gc

import numpy as np
from seqeval.metrics.sequence_labeling import get_entities
from app.utils.materials import corpus_of_value
from app.utils.paramSQL import get_all_MET

from transformers import BertTokenizer, AutoModelForTokenClassification,AutoModelForSequenceClassification, AutoTokenizer, AutoModel
import time


async def bert_chinese_classify_startup():
    device = config.device
    label_list = config.intent_recognize_config['label_list']
    tokenizer = BertTokenizer.from_pretrained(config.intent_recognize_config['tokenizer_dir'])
    model = AutoModelForSequenceClassification.from_pretrained(config.intent_recognize_config['model_dir'], num_labels=len(label_list))
    model.to(device)
    model.eval()
    
    return  device,label_list,tokenizer,model

async def bert_english_classify_startup():
    device = config.device
    label_list = config.intent_recognize_config_en['label_list']
    tokenizer = BertTokenizer.from_pretrained(config.intent_recognize_config_en['tokenizer_dir'])
    model = AutoModelForSequenceClassification.from_pretrained(config.intent_recognize_config_en['model_dir'], num_labels=len(label_list))
    model.to(device)
    model.eval()
    
    return  device,label_list,tokenizer,model

async def bert_chinese_control_startup():
    device = config.device
    label_list = config.param_control_config['label_list']
    tokenizer = BertTokenizer.from_pretrained(config.param_control_config['tokenizer_dir'])
    model = AutoModelForSequenceClassification.from_pretrained(config.param_control_config['model_dir'], num_labels=len(label_list))
    model.to(device)
    model.eval()
    
    return  device,label_list,tokenizer,model
    
async def bert_english_control_startup():
    device = config.device
    label_list = config.param_control_config_en['label_list']
    tokenizer = BertTokenizer.from_pretrained(config.param_control_config_en['tokenizer_dir'])
    model = AutoModelForSequenceClassification.from_pretrained(config.param_control_config_en['model_dir'], num_labels=len(label_list))
    model.to(device)
    model.eval()
    
    return  device,label_list,tokenizer,model

async def bert_predict_startup():
    device = config.device
    args = config.Args()
    args.device = device
    tokenizer = BertTokenizer.from_pretrained(args.bert_dir)
    model = AutoModelForTokenClassification.from_pretrained(args.load_dir)
    model.to(device)
    model.eval()
    return device,args,tokenizer,model

async def bge_recommend_embedding_startup():
    device = config.device
    tokenizer = AutoTokenizer.from_pretrained(config.bge_model_path)
    model = AutoModel.from_pretrained(config.bge_model_path)
    model.to(device)
    model.eval()
    return device,tokenizer,model
    


    
async def bert_chinese_classify_shutdown(app:FastAPI):
    del app.state.bert_cn_classify_device
    del app.state.bert_cn_classify_label_list
    del app.state.bert_cn_classify_tokenizer
    del app.state.bert_cn_classify_model
    

async def bert_english_classify_shutdown(app:FastAPI):
    del app.state.bert_en_classify_device
    del app.state.bert_en_classify_label_list
    del app.state.bert_en_classify_tokenizer
    del app.state.bert_en_classify_model
    
async def bert_chinese_control_shutdown(app:FastAPI):
    del app.state.bert_cn_control_device
    del app.state.bert_cn_control_label_list
    del app.state.bert_cn_control_tokenizer
    del app.state.bert_cn_control_model
    
async def bert_english_control_shutdown(app:FastAPI):
    del app.state.bert_en_control_device
    del app.state.bert_en_control_label_list
    del app.state.bert_en_control_tokenizer
    del app.state.bert_en_control_model
    
async def bert_predict_shutdown(app:FastAPI):
    del app.state.bert_predict_device
    del app.state.bert_predict_config
    del app.state.bert_predict_tokenizer
    del app.state.bert_predict_model
    
async def bge_recommend_embedding_shutdown(app:FastAPI):
    del app.state.bge_recommend_embedding_device
    del app.state.bge_recommend_embedding_tokenizer
    del app.state.bge_recommend_embedding_model


@asynccontextmanager
async def start_bert(app: FastAPI):
    # --- 启动阶段：前处理 ---
    # --- 中文意图分流bert ---
    (app.state.bert_cn_classify_device,
    app.state.bert_cn_classify_label_list,
    app.state.bert_cn_classify_tokenizer,
    app.state.bert_cn_classify_model )= await bert_chinese_classify_startup()
    # 把结果挂到 app.state 上，后面路由里可以用
    
    # --- 英文意图分流bert ---
    (app.state.bert_en_classify_device,
    app.state.bert_en_classify_label_list,
    app.state.bert_en_classify_tokenizer,
    app.state.bert_en_classify_model )= await bert_english_classify_startup()
    
    # --- 中文控制bert ---
    (app.state.bert_cn_control_device,
    app.state.bert_cn_control_label_list,
    app.state.bert_cn_control_tokenizer,
    app.state.bert_cn_control_model )= await bert_chinese_control_startup()
    
    # --- 英文控制bert ---
    (app.state.bert_en_control_device,
    app.state.bert_en_control_label_list,
    app.state.bert_en_control_tokenizer,
    app.state.bert_en_control_model )= await bert_english_control_startup()
    
    # --- 预测填字bert ---
    (app.state.bert_predict_device,
    app.state.bert_predict_config,
    app.state.bert_predict_tokenizer,
    app.state.bert_predict_model )= await bert_predict_startup()
    
    # --- 材料厚度推荐BGE---
    # (app.state.bge_recommend_embedding_device,
    # app.state.bge_recommend_embedding_tokenizer,
    # app.state.bge_recommend_embedding_model)= await bge_recommend_embedding_startup()

    # 让应用跑起来
    yield

    # --- 关闭阶段：后处理 ---
    # 这里可以拿到之前的 bert_chinese_classify 结果做收尾
    await bert_chinese_classify_shutdown(app)
    await bert_english_classify_shutdown(app)
    await bert_chinese_control_shutdown(app)
    await bert_english_control_shutdown(app)
    await bert_predict_shutdown(app)
    #await bge_recommend_embedding_shutdown(app)
    gc.collect()
    torch.cuda.empty_cache()


# 把 lifespan 传给 FastAPI 构造函数
bert_app = FastAPI(
    title="StartupBert",
    lifespan=start_bert,
)

#定义传入参数
class ClassificationRequest(BaseModel):  #传入预测模板
    query: str
    exclude: list[str]
    
class ControlRequest(BaseModel):  #传入控制模板
    query: str
    
class PredictReq(BaseModel):
    text:str
    userID:str
    
class RecommendRequest(BaseModel):  #传入控制模板
    texts: list

class Response1(BaseModel): #返回结果模板
    predictions: str 
    
class Response2(BaseModel): #返回结果模板
    predictions: list
    
class  Response_predict(BaseModel): #预测函数结果返回模板
    意图:str
    槽位:str
    
@bert_app.post ("/bert_cn_classify",response_model=Response1)
def bert_cn_classify(reqCN: ClassificationRequest):
    #start_wall = time.time()
    #start_cpu = time.process_time()
    
    inputs = bert_app.state.bert_cn_classify_tokenizer(reqCN.query, padding=True, return_tensors="pt")
    inputs.to(bert_app.state.bert_cn_classify_device)
    print(f"Model device: {next(bert_app.state.bert_cn_classify_model.parameters()).device}")
    print(f"Input device: {inputs['input_ids'].device}")
    with torch.no_grad():
        outputs = bert_app.state.bert_cn_classify_model(**inputs)

    logits = outputs.logits
    for item in reqCN.exclude:
        exclude_index = bert_app.state.bert_cn_classify_label_list.index(item)
        logits[0][exclude_index] = -100
    predicted_classes = torch.argmax(logits, dim=1)
    prediction = bert_app.state.bert_cn_classify_label_list[predicted_classes[0]]
    
    # end_wall = time.time()
    # end_cpu = time.process_time()
    # print("Wall time:", end_wall - start_wall)
    # print("CPU time:", end_cpu - start_cpu)
    
    return Response1(predictions=prediction)

@bert_app.post ("/bert_en_classify",response_model=Response1)
def bert_en_classify(reqCN: ClassificationRequest):
    
    inputs = bert_app.state.bert_en_classify_tokenizer(reqCN.query, padding=True, return_tensors="pt")
    inputs.to(bert_app.state.bert_en_classify_device)
    with torch.no_grad():
        outputs = bert_app.state.bert_en_classify_model(**inputs)

    logits = outputs.logits
    for item in reqCN.exclude:
        exclude_index = bert_app.state.bert_en_classify_label_list.index(item)
        logits[0][exclude_index] = -100
    predicted_classes = torch.argmax(logits, dim=1)
    prediction = bert_app.state.bert_en_classify_label_list[predicted_classes[0]]
    return Response1(predictions=prediction)

@bert_app.post ("/bert_cn_control",response_model=Response1)
def bert_en_classify(reqCN: ControlRequest):
    
    inputs = bert_app.state.bert_cn_control_tokenizer(reqCN.query, padding=True, return_tensors="pt")
    inputs.to(bert_app.state.bert_cn_control_device)
    with torch.no_grad():
        outputs = bert_app.state.bert_cn_control_model(**inputs)

    logits = outputs.logits
    predicted_classes = torch.argmax(logits, dim=1)
    prediction = bert_app.state.bert_cn_control_label_list[predicted_classes[0]]
    return Response1(predictions=prediction)

@bert_app.post ("/bert_en_control",response_model=Response1)
def bert_en_classify(reqCN: ControlRequest):
    
    inputs = bert_app.state.bert_en_control_tokenizer(reqCN.query, padding=True, return_tensors="pt")
    inputs.to(bert_app.state.bert_en_control_device)
    with torch.no_grad():
        outputs = bert_app.state.bert_en_control_model(**inputs)

    logits = outputs.logits
    predicted_classes = torch.argmax(logits, dim=1)
    prediction = bert_app.state.bert_en_control_label_list[predicted_classes[0]]
    return Response1(predictions=prediction)


def get_unit_intent(text):
    for x in ["厘米", "公分", "cm", "CM"]:
        if x in text:
            return "QUERY_CM"
    return "QUERY_MM"

def check_MET(value,userID):
    value_list = corpus_of_value['MET']
    #插入用户定义的方法
    value_list.extend(get_all_MET(userID))
    if any(v in value_list for v in {value, value.upper(), value.lower()}) :
        print("这里有识别到")
        return True    
    else:
        print("这里没有识别到")
        return False


@bert_app.post("/bert_predict",response_model=Response_predict)
def  predict(PRE:PredictReq):
    #注意这里是简单赋值，针对可变对象会变化，不可变对象不变，所以不必担心内存问题
    config = bert_app.state.bert_predict_config
    tokenizer=bert_app.state.bert_predict_tokenizer
    device=bert_app.state.bert_predict_device
    model=bert_app.state.bert_predict_model
    text=PRE.text.lower()
    userID=PRE.userID
    with torch.no_grad():
        inputs = tokenizer.encode_plus(
            text=text,
            max_length=config.max_len,
            padding='max_length',
            truncation='only_first',
            return_attention_mask=True,
            return_tensors='pt'
        )
        for key in inputs.keys():
            inputs[key] = inputs[key].to(device)

        input_ids = inputs['input_ids']
        attention_mask = inputs['attention_mask']

        # 计算输出
        output = model(input_ids, attention_mask)
        output = output.logits.detach().cpu().numpy()
        output = np.argmax(output, -1)
        output = output[0]
        output = [config.id2ner_label[i] for i in output]
        entities = [(i[0], input_ids[0][i[1]:i[2] + 1], i[1], i[2]) for i in get_entities(output)]  # 重点：是拿input_ids和output的logits对应，可千万别拿text[1:-1]去对应
        decoded_entities = []
        for entity in entities:
            entity_list = list(entity)
            entity_list[1] = tokenizer.decode(entity[1]).replace(' ', '')  # 注意，中文模型要.replace(' ', '')，英文是不加的，应为英文单词之间得空格
            # 如果焊接方法不在语料库里，刨掉
            if entity_list[0] == 'MET':
                if check_MET(entity_list[1],userID):
                    decoded_entities.append(tuple(entity_list))
            elif entity_list[1] not in ['[CLS]', '[SEP]']:  # 有时候会抽风，把这两个东西标注为实体
                decoded_entities.append(tuple(entity_list))
        print(decoded_entities)
    return Response_predict(意图=get_unit_intent(text),槽位=str(decoded_entities))
        
# @bert_app.post("/bge_recommend_embedding",response_model=Response2)
# def get_embeddings(Rec:RecommendRequest): 
#     device=bert_app.state.bge_recommend_embedding_device
#     tokenizer=bert_app.state.bge_recommend_embedding_tokenizer
#     model=bert_app.state.bge_recommend_embedding_model
#     inputs = tokenizer(Rec.texts, padding=True, truncation=True, return_tensors='pt',max_length=512)
#     inputs.to(device)
#     with torch.no_grad():
#         outputs = model(**inputs)
#     # 取 [CLS] 标记的输出作为句子的表示
#     embeddings = outputs.last_hidden_state[:, 0, :]
#     return Response2(predictions=embeddings.detach().cpu().tolist())


import inspect        
def main():
    print("程序开始执行")
    model = AutoModelForTokenClassification.from_pretrained(config.Args().load_dir)
    print(model.__class__)
    print(inspect.signature(model.forward))
    help(model.forward)  
    print("程序执行完成")

if __name__ == "__main__":
    main()










