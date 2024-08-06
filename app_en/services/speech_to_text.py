import asyncio
import os

import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread

from fastapi import UploadFile, File

from app.config import config

STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识

# APPID = 'ff9d26aa'
# APISecret = 'YTlhZDY0M2ZhYzk4ZjcwMGMyMDhhYThj'
# APIKey = 'd78a8f15d26324aacc0614a4e16a8b50'
APPID = config.XF_APPID
APISecret = config.XF_APISecret
APIKey = config.XF_APIKey
result = ""

class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, AudioFile):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.AudioFile = AudioFile

        # 公共参数(common)
        self.CommonArgs = {"app_id": self.APPID}
        # 业务参数(business)，更多个性化参数可在官网查看
        self.BusinessArgs = {"domain": "iat", "language": "zh_cn", "accent": "mandarin", "vinfo": 1, "vad_eos": 10000}

    # 生成url
    def create_url(self):
        url = 'wss://ws-api.xfyun.cn/v2/iat'
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }
        # 拼接鉴权参数，生成url
        url = url + '?' + urlencode(v)
        # print("date: ",date)
        # print("v: ",v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        # print('websocket url :', url)
        return url


# 收到websocket消息的处理
def on_message(ws, message):
    try:
        code = json.loads(message)["code"]
        sid = json.loads(message)["sid"]
        if code != 0:
            errMsg = json.loads(message)["message"]
            print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))

        else:
            data = json.loads(message)["data"]["result"]["ws"]
            # print(json.loads(message))
            global result
            for i in data:
                for w in i["cw"]:
                    result += w["w"]
            print("sid:%s call success!,data is:%s" % (sid, json.dumps(data, ensure_ascii=False)))
    except Exception as e:
        print("receive msg,but parse exception:", e)


# 收到websocket错误的处理
def on_error(ws, error):
    print("### error:", error)


# 收到websocket关闭的处理
def on_close(ws, a, b):
    print("### closed ###")

def speech2text(audio_file):
    # 测试时候在此处正确填写相关信息即可运行
    wsParam = Ws_Param(APPID=APPID, APISecret=APISecret,
                       APIKey=APIKey,
                       AudioFile=audio_file)
    websocket.enableTrace(False)
    wsUrl = wsParam.create_url()
    global result
    result = ""
    ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)

    # 收到websocket连接建立的处理
    def on_open(ws):
        def run(*args):
            frameSize = 8000  # 每一帧的音频大小
            intervel = 0.04  # 发送音频间隔(单位:s)
            status = STATUS_FIRST_FRAME  # 音频的状态信息，标识音频是第一帧，还是中间帧、最后一帧

            with open(wsParam.AudioFile, "rb") as fp:
                while True:
                    buf = fp.read(frameSize)
                    # 文件结束
                    if not buf:
                        status = STATUS_LAST_FRAME
                    # 第一帧处理
                    # 发送第一帧音频，带business 参数
                    # appid 必须带上，只需第一帧发送
                    if status == STATUS_FIRST_FRAME:

                        d = {"common": wsParam.CommonArgs,
                             "business": wsParam.BusinessArgs,
                             "data": {"status": 0, "format": "audio/L16;rate=16000",
                                      "audio": str(base64.b64encode(buf), 'utf-8'),
                                      "encoding": "raw"}}
                        d = json.dumps(d)
                        ws.send(d)  # TODO:用await发送socket请求
                        status = STATUS_CONTINUE_FRAME
                    # 中间帧处理
                    elif status == STATUS_CONTINUE_FRAME:
                        d = {"data": {"status": 1, "format": "audio/L16;rate=16000",
                                      "audio": str(base64.b64encode(buf), 'utf-8'),
                                      "encoding": "raw"}}
                        ws.send(json.dumps(d))  # TODO:用await发送socket请求
                    # 最后一帧处理
                    elif status == STATUS_LAST_FRAME:
                        d = {"data": {"status": 2, "format": "audio/L16;rate=16000",
                                      "audio": str(base64.b64encode(buf), 'utf-8'),
                                      "encoding": "raw"}}
                        ws.send(json.dumps(d))  # TODO:用await发送socket请求
                        time.sleep(1)
                        break
                    # 模拟音频采样间隔
                    time.sleep(intervel)
            ws.close()

        thread.start_new_thread(run, ())
    ws.on_open = on_open
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    while True:
        old_result = result
        time.sleep(3)
        if old_result == result:
            break
    return result

# import asyncio
# import websockets
# import base64
# import json
# import ssl
#
# async def speech2text(audio_file):
#     wsParam = Ws_Param(APPID=APPID, APISecret=APISecret,
#                        APIKey=APIKey,
#                        AudioFile=audio_file)
#     wsUrl = wsParam.create_url()
#     global result
#     result = ""
#     ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
#
#     async with websockets.connect(wsUrl, ssl=ssl.SSLContext()) as ws:
#         frameSize = 8000  # 每一帧的音频大小
#         intervel = 0.04  # 发送音频间隔(单位:s)
#         status = STATUS_FIRST_FRAME  # 音频的状态信息
#
#         with open(wsParam.AudioFile, "rb") as fp:
#             while True:
#                 buf = fp.read(frameSize)
#                 if not buf:
#                     status = STATUS_LAST_FRAME
#
#                 if status == STATUS_FIRST_FRAME:
#                     d = {"common": wsParam.CommonArgs,
#                          "business": wsParam.BusinessArgs,
#                          "data": {"status": 0, "format": "audio/L16;rate=16000",
#                                   "audio": str(base64.b64encode(buf), 'utf-8'),
#                                   "encoding": "raw"}}
#                 elif status == STATUS_CONTINUE_FRAME:
#                     d = {"data": {"status": 1, "format": "audio/L16;rate=16000",
#                                   "audio": str(base64.b64encode(buf), 'utf-8'),
#                                   "encoding": "raw"}}
#                 elif status == STATUS_LAST_FRAME:
#                     d = {"data": {"status": 2, "format": "audio/L16;rate=16000",
#                                   "audio": str(base64.b64encode(buf), 'utf-8'),
#                                   "encoding": "raw"}}
#
#                 await ws.send(json.dumps(d))
#
#                 if status == STATUS_LAST_FRAME:
#                     break  # 退出循环
#
#                 status = STATUS_CONTINUE_FRAME if status == STATUS_FIRST_FRAME else status
#                 await asyncio.sleep(intervel)
#
#     return result



speech_dir = config.SPEECH_DIR
os.makedirs(speech_dir, exist_ok=True)

async def save_speech_file(file: UploadFile = File(...)):
    # 获取文件名和内容类型
    filename = file.filename
    content_type = file.content_type
    # 在控制台打印文件信息
    print(f"Received file {filename} with content type {content_type}")
    # 在上传文件夹中创建一个新文件
    date_and_time = str(datetime.now())
    date_and_time = date_and_time.replace(" ", "").replace(".", "").replace("-", "").replace(":", "")
    file_path = os.path.join(speech_dir, f"{date_and_time}_{filename}")
    with open(file_path, "wb") as f:
        # 循环读取上传文件的内容，并写入新文件
        while True:
            # 每次读取4KB的数据
            chunk = await file.read(4096)
            # 如果没有数据，说明文件已经读完，跳出循环
            if not chunk:
                break
            # 写入新文件
            f.write(chunk)
    # 返回一个JSON响应，包含文件名和内容类型
    return {"filename": filename, "content_type": content_type, "file_path": file_path}

if __name__ == "__main__":
    output = speech2text("/dev_data_2/zkyao/code/data/speech/铝九十九点五.pcm")
    print(output)