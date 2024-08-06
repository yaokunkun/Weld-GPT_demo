from app.utils.entity2SQL import get_index_and_thickness_SQL, insert_SQL, update_SQL
from app.models.Parameter import Params
from app.utils.entity2SQL import get_all_dataIndex

def get_index_and_thickness(MET, MAT, DIA):
    return get_index_and_thickness_SQL(MET, MAT, DIA)

def add(MET, MAT, THI, DIA, paramIndex, parampairs):
    params = Params(DataIndex=max(get_all_dataIndex(), key=lambda x:x[0])[0]+1, WeldingMethod=MET, WeldingMaterial=MAT, WireDiameter=DIA, ParamIndex = paramIndex,
                    ParamName="Guideline value for material", ParamValue=THI)
    result = insert_SQL(params)
    if result is None:
        return "数据添加失败！"
    for paramName, paramValue in parampairs.items():
        params = Params(DataIndex=max(get_all_dataIndex(), key=lambda x: x[0])[0] + 1, WeldingMethod=MET,
                        WeldingMaterial=MAT, WireDiameter=DIA, ParamIndex=paramIndex,
                        ParamName=paramName, ParamValue=paramValue)
        result = insert_SQL(params)
        if result is None:
            return "数据添加失败！"
    return "数据添加成功！"

def update(MET, MAT, DIA, paramIndex, parampairs):
    for paramName, paramValue in parampairs.items():
        params = Params(WeldingMethod=MET,
                        WeldingMaterial=MAT, WireDiameter=DIA, ParamIndex=paramIndex,
                        ParamName=paramName, ParamValue=paramValue)
        result = update_SQL(params)
        if result is None:
            return "数据添加失败！"
    return "数据添加成功！"