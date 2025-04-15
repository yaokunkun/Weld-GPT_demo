from datetime import datetime
from wsgiref.handlers import format_date_time
from time import mktime
import hashlib
import base64
import hmac
from urllib.parse import urlencode
import json
import requests
import fasttext
from app.config import config
from app.utils.materials import corpus_of_value, number_values

number_values_list = sum([value for value in number_values.values()], [])
corpus_of_value_list =  sum([value for value in corpus_of_value.values()], [])
corpus_list = number_values_list + corpus_of_value_list

model = fasttext.load_model(config.fast_text_moedel_path)
'''
1.机器翻译2.0，请填写在讯飞开放平台-控制台-对应能力页面获取的APPID、APISecret、APIKey。
 2.目前仅支持中文与其他语种的互译，不包含中文的两个语种之间不能直接翻译。
 3.翻译文本不能超过5000个字符，即汉语不超过15000个字节，英文不超过5000个字节。
 4.此接口调用返回时长上有优化、通过个性化术语资源使用可以做到词语个性化翻译、后面会支持更多的翻译语种。
'''
APPId = 'ff9d26aa'
APISecret = 'YTlhZDY0M2ZhYzk4ZjcwMGMyMDhhYThj'
APIKey = 'd78a8f15d26324aacc0614a4e16a8b50'

# 术语资源唯一标识，请根据控制台定义的RES_ID替换具体值，如不需术语可以不用传递此参数
# RES_ID = "its_en_cn_word"


class AssembleHeaderException(Exception):
    def __init__(self, msg):
        self.message = msg


class Url:
    def __init__(self, host, path, schema):
        self.host = host
        self.path = path
        self.schema = schema
        pass


# calculate sha256 and encode to base64
def sha256base64(data):
    sha256 = hashlib.sha256()
    sha256.update(data)
    digest = base64.b64encode(sha256.digest()).decode(encoding='utf-8')
    return digest


def parse_url(requset_url):
    stidx = requset_url.index("://")
    host = requset_url[stidx + 3:]
    schema = requset_url[:stidx + 3]
    edidx = host.index("/")
    if edidx <= 0:
        raise AssembleHeaderException("invalid request url:" + requset_url)
    path = host[edidx:]
    host = host[:edidx]
    u = Url(host, path, schema)
    return u


# build websocket auth request url
def assemble_ws_auth_url(requset_url, method="POST", api_key="", api_secret=""):
    u = parse_url(requset_url)
    host = u.host
    path = u.path
    now = datetime.now()
    date = format_date_time(mktime(now.timetuple()))
    # print(date)
    # date = "Thu, 12 Dec 2019 01:57:27 GMT"
    signature_origin = "host: {}\ndate: {}\n{} {} HTTP/1.1".format(host, date, method, path)
    # print(signature_origin)
    signature_sha = hmac.new(api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                             digestmod=hashlib.sha256).digest()
    signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
    authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
        api_key, "hmac-sha256", "host date request-line", signature_sha)
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
    # print(authorization_origin)
    values = {
        "host": host,
        "date": date,
        "authorization": authorization
    }

    return requset_url + "?" + urlencode(values)


def translate(text, source_language='en'):
    TEXT = text
    url = 'https://itrans.xf-yun.com/v1/its'
    body = {
        "header": {
            "app_id": APPId,
            "status": 3,
            # "res_id": RES_ID
        },
        "parameter": {
            "its": {
                "from": source_language,
                "to": "cn",
                "result": {}
            }
        },
        "payload": {
            "input_data": {
                "encoding": "utf8",
                "status": 3,
                "text": base64.b64encode(TEXT.encode("utf-8")).decode('utf-8')
            }
        }
    }

    request_url = assemble_ws_auth_url(url, "POST", APIKey, APISecret)
    headers = {'content-type': "application/json", 'host': 'itrans.xf-yun.com', 'app_id': APPId}
    response = requests.post(request_url, data=json.dumps(body), headers=headers)
    tempResult = json.loads(response.content.decode())
    result_dict = json.loads(base64.b64decode(tempResult['payload']['result']['text']).decode())
    result = result_dict['trans_result']['dst']
    return result

def translate_to(text, target_language='en'):
    TEXT = text
    url = 'https://itrans.xf-yun.com/v1/its'
    body = {
        "header": {
            "app_id": APPId,
            "status": 3,
            # "res_id": RES_ID
        },
        "parameter": {
            "its": {
                "from": "cn",
                "to": target_language,
                "result": {}
            }
        },
        "payload": {
            "input_data": {
                "encoding": "utf8",
                "status": 3,
                "text": base64.b64encode(TEXT.encode("utf-8")).decode('utf-8')
            }
        }
    }

    request_url = assemble_ws_auth_url(url, "POST", APIKey, APISecret)
    headers = {'content-type': "application/json", 'host': 'itrans.xf-yun.com', 'app_id': APPId}
    response = requests.post(request_url, data=json.dumps(body), headers=headers)
    tempResult = json.loads(response.content.decode())
    result_dict = json.loads(base64.b64decode(tempResult['payload']['result']['text']).decode())
    result = result_dict['trans_result']['dst']
    return result

def is_chinese_char(char):
    # 判断字符是否在中文的Unicode范围内
    return '\u4e00' <= char <= '\u9fff'

def is_english_char(char):
    # 判断字符是否是英文字符
    return char.isascii() and char.isalpha()

def directly_judge_language(s):
    if s in corpus_list:
        return "cn"
    for char in s:
        unicode_val = ord(char)
        # Check if the character falls in the Hiragana or Katakana range
        if 0x3040 <= unicode_val <= 0x309F or 0x30A0 <= unicode_val <= 0x30FF:
            return "ja"
    return "un"
    
def check_language(s):
    has_chinese = any(is_chinese_char(c) for c in s)

    if has_chinese:
        return "cn"

    else:
        result = model.predict(s)
        ret = result[0][0][9:11]
        # (('__label__fra_Latn',), array([0.99949151]))
        if ret == 'en':
            return "en"
        elif ret == 'fr':
            return "fr"
        elif ret == 'de':
            return "de"
        elif ret == 'sp':
            return "es"
        elif ret == 'po':
            if result[0][0][9:12] == 'pol':  # 波兰语
                return "pl"
            elif result[0][0][9:12] == 'por':  # 葡萄牙语
                return "pt"
            else:
                return "un"
        elif ret == 'ru':
            return "ru"
        elif ret == 'ko':
            return "ko"
        elif ret == 'ar':
            return "ar"
        elif ret == 'nl':
            return "nl"
        elif ret == 'po':
            return "pl"
        elif ret == 'sw':
            return "sv"
        elif ret == 'hu':
            return "hu"
        else:
            return "un"