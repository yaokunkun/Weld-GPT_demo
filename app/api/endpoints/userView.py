import ast
from fastapi import HTTPException, APIRouter, Body
from app.services.userService import add, update, login
from app.services import userService

router = APIRouter()

@router.post("/user/add", response_model=dict)
def add_user(UserName, Password, PhoneNumber, UserRole):
    return add(UserName, Password, PhoneNumber, UserRole)

@router.post("/user/update", response_model=dict)
def update_user(userID, NewUserName="", NewPassword="", NewPhoneNumber="", NewUserRole=""):
    return update(userID, NewUserName, NewPassword, NewPhoneNumber, NewUserRole)

@router.post("/user/login", response_model=dict)
def login_user(UserName="", Password="", PhoneNumber=""):
    return login(UserName, Password, PhoneNumber)


@router.post("/user/send_message", response_model=dict)
def send_message(PhoneNumber):
    return userService.send_message(PhoneNumber)