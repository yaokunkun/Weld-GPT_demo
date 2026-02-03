import json
import secrets
import time
from urllib import parse

import requests

from app.models.User import User
from app.utils.userSQL import get_all_userID, insert_SQL, select_SQL_by_userID, update_SQL, login_by_userName, login_by_PhoneNumber, update_password
from app.utils.encryption import hash_password, check_password
from app.utils.aliyunSendSms import Sample
from app.utils import userSQL

# 20260126 验证码有效期5分钟，冷却时间60秒及新增验证码存储字典
_SMS_CODE_TTL_SECONDS = 300
_SMS_CODE_COOLDOWN_SECONDS = 60
_SMS_CODE_STORE = {}
# 20260126 新增验证码生成函数
def _generate_sms_code(length=6):
    return "".join(str(secrets.randbelow(10)) for _ in range(length))

def _set_sms_code(phone_number, code):
    now = time.time()
    _SMS_CODE_STORE[phone_number] = {
        "code": code,
        "expires_at": now + _SMS_CODE_TTL_SECONDS,
        "last_sent_at": now,
    }
# 20260126 新增验证码获取函数
def _get_sms_record(phone_number):
    record = _SMS_CODE_STORE.get(phone_number)
    if not record:
        return None
    if time.time() > record["expires_at"]:
        _SMS_CODE_STORE.pop(phone_number, None)
        return None
    return record
# 20260126 新增验证码验证函数
def _verify_sms_code(phone_number, code):
    record = _get_sms_record(phone_number)
    if not record:
        return False, "验证码未发送或已过期！"
    if str(code) != str(record["code"]):
        return False, "验证码错误！"
    _SMS_CODE_STORE.pop(phone_number, None)
    return True, "ok"

def add(UserName, Password, PhoneNumber, UserRole, VerifyCode):
    ok, msg = _verify_sms_code(PhoneNumber, VerifyCode)
    if not ok:
        return {"info": msg}
    user = User(UserID=max(get_all_userID(), key=lambda x:x[0])[0]+1,
                UserName=UserName, Password=Password, PhoneNumber=PhoneNumber, UserRole=UserRole)
    user.Password = hash_password(user.Password)
    print(user.Password)
    result = insert_SQL(user)
    if result is None:
        return {'info': "用户添加失败！"}
    return {'info': "用户添加成功！"}

def update(userID, UserName, Password, PhoneNumber, UserRole):
    result = select_SQL_by_userID(userID)[0]
    user = User(UserID=userID)
    user.UserName = result[1] if UserName == "" else UserName
    user.Password = result[2] if Password == "" else Password
    if Password != "":
        user.Password = hash_password(user.Password)
    user.PhoneNumber = result[3] if PhoneNumber == "" else PhoneNumber
    user.UserRole = result[4] if UserRole == "" else UserRole
    result = update_SQL(user)
    if result is None:
        return {'info': "用户信息修改失败！"}
    return {'info': "用户信息修改成功！"}

def login(UserName, Password, PhoneNumber):
    
    if UserName != "":
        result = login_by_userName(UserName, Password)
    else:
        result = login_by_PhoneNumber(PhoneNumber, Password)
    if result is None or len(result) == 0:
        return {'info': "用户名或手机号不存在！", 'userID':-1}
    else:
        for userID, hashed_Password in result:
            if check_password(hashed_Password, Password):
                user = select_SQL_by_userID(userID)[0]
                return {'info': "登录成功！", 'userID': userID, 'userName': user[1], 'phoneNumber': user[3],'userRole': user[4]}
        return {'info': "密码错误！", 'userID':-1, 'userName': -1, 'phoneNumber': -1,'userRole': -1}

def send_message(phoneNumber):
    if not phoneNumber:
        return {"info": "手机号不能为空！"}
    now = time.time()
    record = _SMS_CODE_STORE.get(phoneNumber)
    if record and now - record.get("last_sent_at", 0) < _SMS_CODE_COOLDOWN_SECONDS:
        return {"info": "验证码发送过于频繁，请在上次请求的60秒后再试！"}
    code = _generate_sms_code()
    try:
        result = Sample.main(code, phoneNumber)
    except Exception:
        return {"info": "验证码发送失败！"}
    if result is None or getattr(result, "status_code", None) != 200:
        return {"info": "验证码发送失败！"}
    _set_sms_code(phoneNumber, code)
    return {"info": "验证码发送成功！"}
    
def update_password(phoneNumber, newPassword, VerifyCode):
    ok, msg = _verify_sms_code(phoneNumber, VerifyCode)
    if not ok:
        return {"info": msg, "userID": -1}
    hashed_password = hash_password(newPassword)
    userSQL.update_password(phoneNumber, hashed_password)
    result = login_by_PhoneNumber(phoneNumber, newPassword)
    if result is None or len(result) == 0:
        return {'info': "用户密码修改失败！", 'userID': -1}
    userID = result[0][0]
    return {'info': "用户密码修改成功！", 'userID': userID}
