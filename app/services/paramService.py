from app.utils.paramSQL import get_index_and_thickness_SQL, insert_SQL, update_SQL
from app.models.Param import Param
from app.utils.paramSQL import get_all_dataIndex
from app.models.UserParam import UserParam
from app.utils.userParamSQL import get_all_userDataIndex, get_value_from_dataIndex
from app.utils import paramSQL
from app.utils import userParamSQL

def get_index_and_thickness(MET, MAT, DIA):
    return get_index_and_thickness_SQL(MET, MAT, DIA)

def add(MET, MAT, THI, DIA, paramIndex, parampairs, userID):
    param = Param(DataIndex=max(get_all_dataIndex(), key=lambda x:x[0])[0]+1,
                  WeldingMethod=MET, WeldingMaterial=MAT, WireDiameter=DIA, ParamIndex = paramIndex,
                  ParamName="Guideline value for material", ParamValue=-100)
    userDataIndex = max(get_all_userDataIndex(), key=lambda x:x[0])[0]+1 if len(get_all_userDataIndex()) > 0 else 0
    userParam = UserParam(UserDataIndex=userDataIndex,
                          UserID=userID, DataIndex=param.DataIndex, DataValue=THI)
    result1 = paramSQL.insert_SQL(param)
    result2 = userParamSQL.insert_SQL(userParam)
    if result1 is None or result2 is None:
        return {'info': "数据添加失败！"}
    for paramName, paramValue in parampairs.items():
        if paramName == "Guideline value for material":
            continue
        param = Param(DataIndex=max(get_all_dataIndex(), key=lambda x: x[0])[0] + 1, WeldingMethod=MET,
                        WeldingMaterial=MAT, WireDiameter=DIA, ParamIndex=paramIndex,
                        ParamName=paramName, ParamValue=-100)
        userParam = UserParam(UserDataIndex=max(get_all_userDataIndex(), key=lambda x: x[0])[0] + 1,
                              UserID=userID, DataIndex=param.DataIndex, DataValue=paramValue)
        result1 = paramSQL.insert_SQL(param)
        result2 = userParamSQL.insert_SQL(userParam)

        if result1 is None or result2 is None:
            return {'info': "数据添加失败！"}
    return {'info': "数据添加成功！"}

def update(MET, MAT, DIA, paramIndex, parampairs, userID):
    for paramName, paramValue in parampairs.items():
        param = Param(WeldingMethod=MET,
                        WeldingMaterial=MAT, WireDiameter=DIA, ParamIndex=paramIndex,
                        ParamName=paramName, ParamValue=paramValue)
        dataIndex = paramSQL.get_data_ID(param)[0][0]
        userParam = UserParam(DataIndex=dataIndex, UserID=userID, DataValue=paramValue)
        userDataIndex = userParamSQL.get_userDataIndex(userParam)
        if userDataIndex is None:
            userParam.UserDataIndex=max(get_all_userDataIndex(), key=lambda x:x[0])[0]+1
            result = userParamSQL.insert_SQL(userParam)
        else:
            result = userParamSQL.update_SQL(userParam)
        if result is None:
            return {'info': "数据修改失败！"}
    return {'info': "数据修改成功！"}

def convert_slot_to_true_value(userID, data_index):
    result = get_value_from_dataIndex(userID, data_index)
    if len(result) == 0:
        return -100
    else:
        return result[0][0]