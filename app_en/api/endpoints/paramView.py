import ast
from fastapi import HTTPException, APIRouter, Body
from app.services.paramService import get_index_and_thickness, add, update

router = APIRouter()

@router.post("/add_and_update", response_model=dict)
def add_and_update(userID, method, material, thickness, diameter, params):
    params = ast.literal_eval(params)
    # 1.先根据`WeldingMethod`、`WeldingMaterial`、`WireDiameter`，来**查询**目前有哪些`ParamIndex`
    index_and_thickness = get_index_and_thickness(method, material, diameter)
    # 2.返回的结果如果为空，则调用**增加功能**，当前的`ParamIndex`为1；
    # 如果不为空，再判断当前的焊接厚度是否包含在其中：如果包含，则调用**更新功能**，`ParamIndex`为其厚度所在的；
    # 反之则调用**增加功能**，`ParamIndex`为当前最大值+1。
    if index_and_thickness is None or len(index_and_thickness) == 0:  # 如果返回结果为空  TODO:改成index_and_indexes，拿index再去用户数据表里得知焊接厚度
        paramIndex = 1
        return add(method, material, thickness, diameter, paramIndex, params, userID)
    else:  # 如果返回结果不为空
        candidate_paramIndex = [x[0] for x in index_and_thickness if x[1] == thickness]  # 判断焊接厚度在不在刚才的结果里，如果在并取出对应的paramIndex
        if len(candidate_paramIndex) != 0:  # 如果焊接厚度在刚才的返回结果里面
            paramIndex = candidate_paramIndex[0]
            return update(method, material, diameter, paramIndex, params, userID)
        else:
            paramIndex = max(index_and_thickness, key=lambda x:x[0])[0] + 1
            return add(method, material, thickness, diameter, paramIndex, params, userID)