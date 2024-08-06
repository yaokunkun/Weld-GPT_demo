import ast
from fastapi import HTTPException, APIRouter, Body
from app_en.services.userService import add, update, login

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

