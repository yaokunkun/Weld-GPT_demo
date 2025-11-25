import os
# os.environ["CUDA_VISIBLE_DEVICES"] = '0'

import torch
from transformers import BertTokenizer
from config import Args
from model import BertForIntentAndSlot
from main import Trainer

import base64
import hashlib
import hmac
import json
import os
import time
import requests
import urllib

lfasr_host = 'https://raasr.xfyun.cn/v2/api'
# 请求的接口名
api_upload = '/upload'
api_get_result = '/getResult'


def arabic_num(chi):
    if chi == '零':
        return '0'
    elif chi == '一':
        return '1'
    elif chi == '二':
        return '2'
    elif chi == '三':
        return '3'
    elif chi == '四':
        return '4'
    elif chi == '五':
        return '5'
    elif chi == '六':
        return '6'
    elif chi == '七':
        return '7'
    elif chi == '八':
        return '8'
    elif chi == '九':
        return '9'
    elif chi == '点':
        return '.'
    return chi


class RequestApi(object):
    def __init__(self, appid, secret_key, upload_file_path):
        self.appid = appid
        self.secret_key = secret_key
        self.upload_file_path = upload_file_path
        self.ts = str(int(time.time()))
        self.signa = self.get_signa()

    def get_signa(self):
        appid = self.appid
        secret_key = self.secret_key
        m2 = hashlib.md5()
        m2.update((appid + self.ts).encode('utf-8'))
        md5 = m2.hexdigest()
        md5 = bytes(md5, encoding='utf-8')
        # 以secret_key为key, 上面的md5为msg， 使用hashlib.sha1加密结果为signa
        signa = hmac.new(secret_key.encode('utf-8'), md5, hashlib.sha1).digest()
        signa = base64.b64encode(signa)
        signa = str(signa, 'utf-8')
        return signa


    def upload(self):
        # print("上传部分：")
        upload_file_path = self.upload_file_path
        file_len = os.path.getsize(upload_file_path)
        file_name = os.path.basename(upload_file_path)

        param_dict = {}
        param_dict['appId'] = self.appid
        param_dict['signa'] = self.signa
        param_dict['ts'] = self.ts
        param_dict["fileSize"] = file_len
        param_dict["fileName"] = file_name
        param_dict["duration"] = "200"
        # print("upload参数：", param_dict)
        data = open(upload_file_path, 'rb').read(file_len)

        response = requests.post(url =lfasr_host + api_upload+"?"+urllib.parse.urlencode(param_dict),
                                headers = {"Content-type":"application/json"},data=data)
        # print("upload_url:",response.request.url)
        result = json.loads(response.text)
        # print("upload resp:", result)
        return result


    def get_result(self):
        uploadresp = self.upload()
        orderId = uploadresp['content']['orderId']
        param_dict = {}
        param_dict['appId'] = self.appid
        param_dict['signa'] = self.signa
        param_dict['ts'] = self.ts
        param_dict['orderId'] = orderId
        param_dict['resultType'] = "transfer,predict"
        # print("")
        # print("查询部分：")
        # print("get result参数：", param_dict)
        status = 3
        # 建议使用回调的方式查询结果，查询接口有请求频率限制
        while status == 3:
            response = requests.post(url=lfasr_host + api_get_result + "?" + urllib.parse.urlencode(param_dict),
                                     headers={"Content-type": "application/json"})
            # print("get_result_url:",response.request.url)
            result = json.loads(response.text)
            # print(result)
            status = result['content']['orderInfo']['status']
            print("status=",status)
            if status == 4:
                break
            time.sleep(5)
        # print("get_result resp:", result)

        textss = eval(result['content']['orderResult'])["lattice2"]
        text = ""
        for texts in textss:
            for tt in texts["json_1best"]["st"]["rt"][0]["ws"]:
                text += arabic_num(tt["cw"][0]["w"])
        # print(result)
        return text


if __name__ == "__main__":
    args = Args()
    device = torch.device('cuda:3' if torch.cuda.is_available() else 'cpu')
    args.device = device

    tokenizer = BertTokenizer.from_pretrained(args.bert_dir)
    model = BertForIntentAndSlot(args)
    model.load_state_dict(torch.load(args.load_dir))
    model.to(device)

    trainer = Trainer(model, args)

    api = RequestApi(appid="4a2ad8ed",
                     secret_key="768e14b7c3902f48296cb79531c8b1df",
                     upload_file_path=r"./xfyun/audio/test_audio.m4a")
    text = api.get_result()
    print('文本：', text)

    trainer.predict(text, tokenizer)
