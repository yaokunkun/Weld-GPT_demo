from fastapi import FastAPI
import json
# 1. 导入 CORS 中间件
from fastapi.middleware.cors import CORSMiddleware

logs= FastAPI(title="events_read")

# 2. 配置允许的源（你的前端地址）
origins = [
    "*",  # 明确指定你的前端地址
]

# 3. 添加中间件到应用中
logs.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许的源列表
    allow_credentials=True, # 允许携带 Cookie（如果不需要可以设为 False）
    allow_methods=["GET", "OPTIONS"], # 允许的 HTTP 方法（对应你要求的 GET 和 OPTIONS）
    allow_headers=["Content-Type"],   # 允许的请求头（对应你要求的 Content-Type）
)

# 4. 定义一个测试接口
@logs.get("/api/test")
async def test():
    return {"message": "跨域请求成功！", "data": "Hello from 2035 port"}

@logs.get("/events")
def read_events():
    events = []
    with open("app/events.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            events.append(json.loads(line))
    return events
