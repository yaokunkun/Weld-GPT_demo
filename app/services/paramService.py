from app.utils.paramSQL import  delete_user_param2,delete_user_param_all
from app.utils.paramSQL import insert_user_param,change_user_param,delete_user_param,search_id_user,find_BY_ID
from app.models.Param import Param
from app.models.UserParam import UserParam
from app.utils.userParamSQL import get_all_userDataIndex, get_value_from_dataIndex
from app.utils import paramSQL
from app.utils import userParamSQL




def convert_slot_to_true_value(userID, data_index):
    result = get_value_from_dataIndex(userID, data_index)
    if len(result) == 0:
        return -100
    else:
        return result[0][0]
    
#新实现方法
def add2(userID, method, material, thickness, diameter, parampairs):
    result = None
    for paramName, paramValue in parampairs.items():
        result = insert_user_param(userID, method, material, thickness, diameter, paramName, paramValue)
    if result is None:
        return {'info': "数据添加失败！"}
    else:
        return {'info': "数据添加成功！"}


#2025/11/05 DEBUG UPDATE3
def update3(param_id_map, userID, method, material, thickness, diameter, parampairs):
    """
    使用参数名到ID的映射来更新参数
    param_id_map: {param_name: (ID, USER_ID)} 字典
    """
    for paramName, paramValue in parampairs.items():
        if paramName not in param_id_map:
            return {'info': f"参数 {paramName} 未找到对应的ID，数据修改失败！"}
        param_id = param_id_map[paramName][0]  # 获取ID
        result = change_user_param(param_id, userID, method, material, thickness, diameter, paramName, paramValue)
        if result is None:
            return {'info': f"参数 {paramName} 数据修改失败！"}
    return {'info': "数据修改成功！"}
    
def del2(ID):
    result=delete_user_param(ID)
    if result is None:
        return {'info': "数据删除失败！数据不存在"}
    else:
        return {'info': "数据删除成功！"}
    
def del3(UID,MET,MAT,THI,DIA):
    result=None
    result=delete_user_param2(UID,MET,MAT,THI,DIA)
    if result is None:
        return {'info-del': "数据删除失败！数据不存在"}
    else:
        return {'info-del': "数据删除成功！"}
    
def del_all(UID):
    result=None
    result=delete_user_param_all(UID)
    if result is None:
        return {'info-del': "该用户目前数据库中没有数据!"}
    else:
        return {'info-del': "该用户的数据已经全部删除!"}

def get_id_user2(userID, method, material, thickness, diameter, parampairs):
    for paramName, paramValue in parampairs.items():
        result = search_id_user(userID, method, material, thickness, diameter, paramName,paramValue)
        return result

def get_id_user4(userID, method, material, thickness, diameter):
        result = search_id_user(userID, method, material, thickness, diameter)
        return result



def find_by_userID2(userID):
    return search_id_user(UID=userID)

def find2(IDS):
    resultO=find_BY_ID(IDS)   #  IDS = [(id,user_ID),(1, 100), (2, 100), (3, 100)]  # 来自search_id_user的返回结果
    if not resultO:
        return {'info': "数据不存在！"}
    else:
        # 兜底：过滤空元组，避免 IndexError
        safe_results = [result for result in resultO if result and len(result) > 0]
        if not safe_results:
            return {'info': "数据不存在！"}
        my_dict = {result[0]: result[1:] for result in safe_results}
        return my_dict