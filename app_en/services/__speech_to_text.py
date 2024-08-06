import os
import datetime
from datetime import datetime
from fastapi import UploadFile, File
from app.config import config


# -*- encoding:utf-8 -*-
import hashlib
import hmac
import base64
from socket import *
import json, time, threading
from websocket import create_connection
import websocket
from urllib.parse import quote
import logging

# reload(sys)
# sys.setdefaultencoding("utf8")
APPID = config.XF_APPID
APISecret = config.XF_APISecret
APIKey = config.XF_APIKey

app_id = APPID
api_key = APIKey
class Client():
    def __init__(self):
        base_url = "ws://rtasr.xfyun.cn/v1/ws"
        ts = str(int(time.time()))
        tt = (app_id + ts).encode('utf-8')
        md5 = hashlib.md5()
        md5.update(tt)
        baseString = md5.hexdigest()
        baseString = bytes(baseString, encoding='utf-8')

        apiKey = api_key.encode('utf-8')
        signa = hmac.new(apiKey, baseString, hashlib.sha1).digest()
        signa = base64.b64encode(signa)
        signa = str(signa, 'utf-8')
        self.end_tag = "{\"end\": true}"

        self.ws = create_connection(base_url + "?appid=" + app_id + "&ts=" + ts + "&signa=" + quote(signa))
        self.trecv = threading.Thread(target=self.recv)
        self.trecv.start()

    def send(self, file_path):
        file_object = open(file_path, 'rb')
        try:
            index = 1
            while True:
                chunk = file_object.read(1280)
                if not chunk:
                    break
                self.ws.send(chunk)

                index += 1
                time.sleep(0.04)
        finally:
            file_object.close()

        self.ws.send(bytes(self.end_tag.encode('utf-8')))
        print("send end tag success")

    def recv(self):
        try:
            while self.ws.connected:
                result = str(self.ws.recv())
                if len(result) == 0:
                    print("receive result end")
                    break
                result_dict = json.loads(result)
                # 解析结果
                if result_dict["action"] == "started":
                    print("handshake success, result: " + result)

                if result_dict["action"] == "result":
                    result_1 = result_dict
                    # result_2 = json.loads(result_1["cn"])
                    # result_3 = json.loads(result_2["st"])
                    # result_4 = json.loads(result_3["rt"])
                    print("rtasr result: " + result_1["data"])

                if result_dict["action"] == "error":
                    print("rtasr error: " + result)
                    self.ws.close()
                    return
        except websocket.WebSocketConnectionClosedException:
            print("receive result end")

    def close(self):
        self.ws.close()
        print("connection closed")

client = Client()

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
    print(client.send("/dev_data_2/zkyao/code/data/speech/铝九十九点五.pcm"))
    # print(speech2text("/dev_data_2/zkyao/code/data/speech/铝九十九点五.pcm"))