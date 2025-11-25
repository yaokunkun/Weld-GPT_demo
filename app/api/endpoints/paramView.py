import ast
from fastapi import HTTPException, APIRouter, Body
from app.services.paramService import add2,del3,del2,get_id_user4,find2,find_by_userID2,del_all

router = APIRouter()


@router.post("/find_user_param_data", response_model=dict)
def find_user_param_data(userID):
    return find2(find_by_userID2(userID))

@router.post("/add_user_param_data", response_model=dict)
def add_user_param_data(userID, method, material, thickness, diameter, params):
    params = ast.literal_eval(params)
    # 使用精确匹配来检查是否已存在完全相同的参数组合
    result = get_id_user4(userID, method, material, thickness, diameter)
    
    # 如果没找到完全相同的组合，允许添加
    if not result:
        return add2(userID, method, material, thickness, diameter, params)
    else:
        con={'info': "查询到同名数据，是否删除并更新？","content":""}
        con["content"]=result
        return  con
    

@router.post("/del_user_param_data", response_model=dict)
def del_user_param_data(userID, ID:int):
    IDS=find_by_userID2(userID)
    id_access=[id_pair[0] for id_pair in IDS]
    print (id_access)   
    if ID in id_access:
        return del2(ID)
        
    else:
        return {'info':"您删除的数据,不是你的账户所能删除的"}
    
@router.post("/del_all_user_param_data", response_model=dict)
def del_user_param_data(userID:int):
    return del_all(userID)
    
@router.post("/update_user_param_data", response_model=dict)
def update_user_param_data(userID, method, material, thickness, diameter, params):
    params = ast.literal_eval(params)
    result = get_id_user4(userID, method, material, thickness, diameter)
    # 如果没找到匹配的数据
    if not result:
        return {'info': "您更新的数据不存在"}
    #找到了，就删除
    else:
        information=del3(userID, method, material, thickness, diameter)
        information.update(add2(userID, method, material, thickness, diameter, params))
    return information
