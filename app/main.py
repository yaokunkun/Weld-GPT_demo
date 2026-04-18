import uvicorn
from fastapi import FastAPI, Request,Response,Depends
from app.connection_pool_for_main import http_client
from contextlib import asynccontextmanager
from app.api.init import router as api_router
import logging
from app.config import config
import os
import redis.asyncio as redis_async
from datetime import datetime
import time
import json
import fcntl
from app.sensitive_word import SENSITIVE_WORDS

B_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(B_DIR,"events.jsonl")

# 敏感词列表 - 可以根据实际需求扩展 现已写入单独文件sensitive_word.py
# SENSITIVE_WORDS = [
#     "暴力", "色情", "赌博", "毒品", "政治", "反动", "分裂", "恐怖",
#     "攻击", "破坏", "违法", "犯罪", "诈骗", "传销", "邪教"]

def check_sensitive_words(text: str) -> tuple[bool, str]:
    """
    检查文本是否包含敏感词
    返回: (是否包含敏感词, 匹配到的敏感词)
    """
    if not text:
        return False, ""
    
    text_lower = text.lower()
    for word in SENSITIVE_WORDS:
        if word in text_lower:
            return True, word
    return False, ""

def extract_user_query(request: Request, body_text: str) -> str:
    """
    从请求中提取用户查询内容
    优先从query参数获取，如果没有则尝试从body中解析
    """
    # 1. 尝试从query参数获取
    query = request.query_params.get("query")
    if query:
        return query
    
    # 2. 尝试从POST body中解析JSON
    if body_text:
        try:
            body_json = json.loads(body_text)
            # 常见的查询字段名
            for key in ["query", "text", "input", "question", "content"]:
                if key in body_json:
                    return str(body_json[key])
        except (json.JSONDecodeError, TypeError):
            pass
    
    # 3. 如果都没有，返回body文本（可能是form data或其他格式）
    return body_text if body_text else "" 

# 获取当前时间
now = datetime.now()
# 格式化为指定形式
formatted_time = now.strftime("%Y%m%d%H%M")

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(filename)s : %(levelname)s  %(message)s",
                    datefmt="%Y-%m-%d %A %H:%M:%S",
                    filename=os.path.join(config.LOG_DIR, formatted_time+".log"),  # 日志输出到文件
                    filemode='a')  # 追加模式



#1215-1217 构建httpx连接池 使用一部生命周期函数
#事实证明原来的逻辑写全局函数request访问，这么做会发生循环依赖，要单独写http池，要不然太灾难了

# 创建一个可重用的 httpx 客户端（带连接池）
# 在应用启动时创建，在应用关闭时释放
@asynccontextmanager
async def main_service_lifetime(app:FastAPI):
    await http_client.init()
    app.state.session_redis = None
    try:
        client = redis_async.from_url(
            config.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        await client.ping()
        app.state.session_redis = client
        logging.info("Redis session backend connected: %s", config.REDIS_URL)
    except Exception:
        logging.warning(
            "Redis unavailable; sessions fall back to in-memory (not safe with multiple workers). URL=%s",
            config.REDIS_URL,
            exc_info=True,
        )
    yield
    if getattr(app.state, "session_redis", None) is not None:
        await app.state.session_redis.aclose()
    await http_client.close()

# # 依赖项：获取客户端
# async def http_client_bert():
#     return app.state.http_client_bert


app = FastAPI(title="weldGPT_main_service",lifespan=main_service_lifetime)
app.include_router(api_router, prefix="/api")

# 创建中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    #1212修改部分日志记录，记录输入内容
    
    body_bytes = await request.body()  # 读一次（我们要缓存）
    body_text = body_bytes.decode("utf-8", errors="replace")

    #1212 关键：把 body “放回去”，避免下游读不到
    async def receive():
        return {"type": "http.request", "body": body_bytes, "more_body": False}

    request = Request(request.scope, receive)
    ############################################
    
    # 审核功能：检查用户查询是否包含敏感词
    user_query = extract_user_query(request, body_text)
    audit_time = datetime.now().isoformat()
    has_sensitive_word, matched_word = check_sensitive_words(user_query)
    
    # 如果包含敏感词，直接返回拒绝响应
    if has_sensitive_word:
        audit_status = "REJECTED"
        reject_response = {
            "error": "用户提问不合法",
            "response": "您的问题包含不当内容，请重新提问。"
        }
        response_text = json.dumps(reject_response, ensure_ascii=False)
        response = Response(
            content=response_text,
            status_code=400,
            media_type="application/json"
        )
        # 创建新的response用于返回
        new_response = response
    else:
        audit_status = "PASS"
        response = await call_next(request)
        
        #1126我们来实现一下抓取返回的response 内容，这是最小化开销的写法
        response_text = ""
        # 1. 把 body_iterator 里的内容拉出来
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        # 2. 生成日志用的文本
        try:
            response_text = body.decode("utf-8")
        except UnicodeDecodeError:
            response_text = "<non-utf8 body>"
        
        #4. 用刚刚读出来的 body 重新构造一个 Response 返回
        new_response = Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
                )
        new_response.background = response.background
    
    # 计算处理时间
    process_time = (time.time() - start_time) * 1000    
    
    try:
        logging.info(f"请求路径: {request.url.path}, 请求方法: {request.method}, 客户端地址: {request.client.host}, 完成时间: {process_time:.2f}ms, 响应状态: {new_response.status_code}, 审核状态: {audit_status}; \n 响应内容： {response_text}")
    except Exception as e:
        logging.error(f"日志记录失败: {e}")
        logging.info(f"请求: {request}, 完成时间: {process_time:.2f}ms, 响应状态: {new_response.status_code}, 审核状态: {audit_status}")
    #应付检查的第二日志，不做数据库了，麻烦1212
    MAX_BODY = 2000 
    safe_resp = response_text[:MAX_BODY] + ("...<truncated>" if len(response_text) > MAX_BODY else "")
    #对于替换机器的写法单开一条
    machine_change=""
    if request.query_params.get("old_machine"):
        machine_change=str(request.query_params.get("old_machine"))+" to "+str(request.query_params.get("new_machine"))
    
    # 获取用户查询用于日志记录
    log_query = user_query if user_query else str(request.query_params.get("query"))
    
    events={
        "Time": datetime.now().isoformat(),
        "ip":str(request.client.host),
        "Method":str(request.method),
        "Url":str(request.url.path),
        "Status":str(new_response.status_code),
        "ProcessTime":f"{process_time:.2f}"+"ms",
        "Request":log_query,
        "UID":str(request.query_params.get("userID")),
        "machine":str(request.query_params.get("machine"))+" "+machine_change,
        "Response":safe_resp,
        "AuditStatus":audit_status,  # 审核状态：PASS、PENDING、REJECTED
        "AuditTime":audit_time  # 审核时间
        }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)  #加文件锁1213
        f.write(json.dumps(events, ensure_ascii=False) + "\n")
        f.flush()
        fcntl.flock(f, fcntl.LOCK_UN)
    return new_response


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001)