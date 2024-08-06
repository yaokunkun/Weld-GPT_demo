import json
import random
from urllib import parse

import requests

from app.models.User import User
from app.utils.userSQL import get_all_userID, insert_SQL, select_SQL_by_userID, update_SQL, login_by_userName, login_by_PhoneNumber
from app.utils.encryption import hash_password, check_password
from app.utils.aliyunSendSms import Sample

def add(UserName, Password, PhoneNumber, UserRole):
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
    length = 6
    code = ''
    for i in range(length):
        code += str(random.randint(0, 9))
    result = Sample.main(code, phoneNumber)
    return {'info': '验证码发送成功' if result.status_code == 200 else '验证码发送失败',
            'code':code}