import uvicorn
from fastapi import FastAPI, Request
from app.api.init import router as api_router
import logging
from app.config import config
import os
from datetime import datetime
import time

# 获取当前时间
now = datetime.now()
# 格式化为指定形式
formatted_time = now.strftime("%Y%m%d%H%M")

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(filename)s : %(levelname)s  %(message)s",
                    datefmt="%Y-%m-%d %A %H:%M:%S",
                    filename=os.path.join(config.LOG_DIR, formatted_time+".log"),  # 日志输出到文件
                    filemode='a')  # 追加模式

app = FastAPI()
app.include_router(api_router, prefix="/api")

# 创建中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    logging.info(f"请求路径: {request.url.path}, 请求方法: {request.method}, 客户端地址: {request.client.host}, 完成时间: {process_time:.2f}ms, 响应状态: {response.status_code}")
    return response


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8003)