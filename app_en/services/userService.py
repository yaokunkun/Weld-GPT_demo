import random

from app.models.User import User
from app_en.utils.userSQL import get_all_userID, insert_SQL, select_SQL_by_userID, update_SQL, login_by_userName, login_by_PhoneNumber
import requests
from urllib import parse

def add(UserName, Password, PhoneNumber, UserRole):
    user = User(UserID=max(get_all_userID(), key=lambda x:x[0])[0]+1,
                UserName=UserName, Password=Password, PhoneNumber=PhoneNumber, UserRole=UserRole)
    result = insert_SQL(user)
    if result is None:
        return {'info': "User addition failed!"}
    return {'info': "User addition succeed!"}

def update(userID, UserName, Password, PhoneNumber, UserRole):
    result = select_SQL_by_userID(userID)[0]
    user = User(UserID=userID)
    user.UserName = result[2] if UserName == "" else UserName
    user.Password = result[5] if Password == "" else Password
    user.PhoneNumber = result[-1] if PhoneNumber == "" else PhoneNumber
    user.UserRole = result[7] if UserRole == "" else UserRole
    result = update_SQL(user)
    if result is None:
        return {'info': "User information modification failed!"}
    return {'info': "User information modification succeed!"}

def login(UserName, Password, PhoneNumber):
    if UserName != "":
        result = login_by_userName(UserName, Password)
    else:
        result = login_by_PhoneNumber(PhoneNumber, Password)
    if len(result) == 0:
        return {'info': "Wrong password!", 'userID':-1}
    else:
        return {'info': "Login successfully!", 'userID': result[0][0]}



