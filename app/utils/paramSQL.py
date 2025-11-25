import mysql.connector
from app.config import config

user = config.MYSQL_USER
password = config.MYSQL_PASSWORD
#访问数据库
def access_DB(query):
    try:
            # 连接到 MySQL 数据库
        connection = mysql.connector.connect(
            host="localhost",  # 数据库服务器地址
            port=3306,  # 数据库服务器端口
            user=user,  # 数据库用户名
            password=password,  # 数据库密码
            database="welding"  # 数据库名称
        )

        if connection.is_connected():
            # 创建游标对象
            cursor = connection.cursor()
            # 执行 SQL 查询
            cursor.execute(query)
            # 检索所有行
            result = cursor.fetchall()
            # 提交事务
            connection.commit()

        return result

    except mysql.connector.Error as error:
        print("Error: ", error)

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

#官方表部分
#新SQL查表逻辑
def select_SQL_rec(MET, MAT):  #推荐系统用，看是否只会走厚度推荐
    # 拼接SQL语句
    query = f"""
        SELECT Thickness
        FROM param_data
        WHERE Method = '{MET}'
        AND Material = '{MAT}'
        """
    #连接数据库并执行查询，返回的是元组列表[(Diameter, ParamName, ParamValue)]
    result = access_DB(query)
    return result
def select_SQL(MET, MAT, THI):
    # 拼接SQL语句
    query = f"""
        SELECT Diameter, ParamName, ParamValue
        FROM param_data
        WHERE Method = '{MET}'
        AND Material = '{MAT}'
        AND Thickness = '{THI}'
        """
    #连接数据库并执行查询，返回的是元组列表[(Diameter, ParamName, ParamValue)]
    result = access_DB(query)
    return result
#作用同上一个函数，别名查询（前端要求）
def get_param_by_mat_met_thi(MAT, MET, THI):
    # （一）拼接SQL语句
    query = f"""
        SELECT Diameter, ParamName, ParamValue
        FROM param_data
        WHERE Method = '{MET}'
        AND Material = '{MAT}'
        AND Thickness = '{THI}'
        """

    # （二）连接数据库并执行查询
    result = access_DB(query)

    # （三）返回结果
    return result

def get_all_param_by_MAT_MET(MET, MAT):
    # （一）拼接SQL语句

    query = f"""
        SELECT Thickness, Diameter, ParamName, ParamValue
        FROM param_data
        WHERE Material = '{MAT}'
        AND Method = '{MET}'
        """
    # （二）连接数据库并执行查询
    result = access_DB(query)
    # （三）返回结果。
    # result = [e[0] for e in result]
    return result


###########
#用户表部分
###########

#查找所有厚度
def get_all_THI(userID,MET=None, MAT=None):
    
    if MET is not None:
        if MAT is not None:
            query = f"""SELECT Thickness FROM param_data WHERE Method = '{MET}' AND Material = '{MAT}';"""
            query_user=f"""SELECT Thickness FROM `USER_PARAM_T` WHERE Method = '{MET}' AND Material = '{MAT}' AND user_ID='{userID}';"""
        else:
            query = f"""SELECT Thickness FROM param_data WHERE Method = '{MET}' ;"""
            query_user = f"""SELECT Thickness FROM `USER_PARAM_T` WHERE Method = '{MET}' AND user_ID='{userID}';"""
    elif MAT is not None:
        query = f"""SELECT Thickness FROM param_data WHERE Material = '{MAT}';"""
        query_user = f"""SELECT Thickness FROM `USER_PARAM_T` WHERE Material = '{MAT}' AND user_ID='{userID}';"""
    else:
        query = f"""SELECT Thickness FROM param_data;"""
        query_user = f"""SELECT Thickness FROM `USER_PARAM_T` user_ID='{userID}';"""
    result = access_DB(query)
    result_user = access_DB(query_user)
    result0 = [item[0] for item in result] #元组列表变为列表 列表推导式 
    result1 = list(set(result0))  #去重
    result0_user = [item[0] for item in result_user] #元组列表变为列表 列表推导式 
    result1_user = list(set(result0_user))  #去重
    result1.extend(result1_user)
    return result1

#新增用户表参数
def insert_user_param(UID=None,MET=None,MAT=None,THI=None,DIA=None,PN=None,PV=None):
    if not all([UID,MET,MAT,THI,DIA,PN,PV]):
        return False
    else:
        query= f"""INSERT INTO `USER_PARAM_T`(`USER_ID`,`Method`,`Material` ,`Thickness`,`Diameter`,`ParamName`,`ParamValue`)
        VALUES ({UID},'{MET}','{MAT}',{THI},'{DIA}','{PN}',{PV})"""
        result=access_DB(query)
        return result

#修改用户表参数
def change_user_param(ID=None,UID=None,MET=None,MAT=None,THI=None,DIA=None,PN=None,PV=None):
    if not all([ID,UID,MET,MAT,THI,DIA,PN,PV]):
        return False
    else:
        query= f"""UPDATE `USER_PARAM_T` SET `USER_ID`={UID},`Method`='{MET}',`Material`='{MAT}',`Thickness`={THI},`Diameter`='{DIA}',`ParamName`='{PN}',`ParamValue`={PV} WHERE `ID`={ID}"""
        result=access_DB(query)
        return result

#删除用户表参数
def delete_user_param(ID=None):
    if not ID:
        return False
    else:
        query= f"""DELETE FROM `USER_PARAM_T` WHERE `ID`={ID}"""
        result=access_DB(query)
        return result
    
def delete_user_param2(UID=None,MET=None,MAT=None,THI=None,DIA=None):
    if not all([UID,MET,MAT,THI,DIA]):
        return False
    else:
        query= f"""DELETE FROM `USER_PARAM_T` WHERE `USER_ID`={UID} AND `Method`='{MET}' AND `Material`='{MAT}' AND `Thickness`='{THI}' AND `Diameter`='{DIA}'"""
        result=access_DB(query)
        return result
    
def delete_user_param_all(UID=None):
    if not UID:
        return False
    else:
        query= f"""DELETE FROM `USER_PARAM_T` WHERE `USER_ID`={UID} """
        result=access_DB(query)
        print(result)
        return result

#搜索用户表 通用, 返回id和uid（一对多查询）
def search_id_user(UID=None,MET=None,MAT=None,THI=None,DIA=None,PN=None,PV=None):
    if not UID:
        return [()]
    else:
        query= f"""SELECT ID,USER_ID FROM `USER_PARAM_T` WHERE USER_ID={UID}"""
        CONDITIONS=[]
        if MET:
            CONDITIONS.append(f"Method='{MET}'")
        if MAT:
            CONDITIONS.append(f"Material='{MAT}'")
        if THI:
            CONDITIONS.append(f"Thickness={THI}")
        if DIA:
            CONDITIONS.append(f"Diameter='{DIA}'")
        if PN:
            CONDITIONS.append(f"ParamName='{PN}'")
        if PV:
            CONDITIONS.append(f"ParamValue={PV}")
        if CONDITIONS:
            query= query+ " AND " +' AND '.join(CONDITIONS)
        result=access_DB(query)
        return result
########################################################
#通过id和uid组查询返回所有参数（多组查询）
def find_BY_ID(IDS):   #  IDS = [(id,user_ID),(1, 100), (2, 100), (3, 100)]  # 来自search_id_user的返回结果
    if not IDS:
        return [()]
    else:
        RESULTS=[]
        for ID in IDS:
            query= f"""SELECT * FROM `USER_PARAM_T` WHERE ID={ID[0]}"""
            result=access_DB(query)
            RESULTS.append(result[0])
        return RESULTS

#三要素 材料厚度方法 查询用户表
def select_user_SQL(MET, MAT, THI,userID):
    # 拼接SQL语句
    query = f"""
        SELECT Diameter, ParamName, ParamValue
        FROM `USER_PARAM_T`
        WHERE Method = '{MET}'
        AND Material = '{MAT}'
        AND Thickness = {THI}
        AND User_ID = '{userID}'
        """
    #连接数据库并执行查询，返回的是元组列表[(Diameter, ParamName, ParamValue)]
    result = access_DB(query)
    return result   

def select_user_THI(MET, MAT,userID):
    # 拼接SQL语句
    query = f"""
        SELECT Thickness
        FROM `USER_PARAM_T`
        WHERE Method = '{MET}'
        AND Material = '{MAT}'
        AND User_ID = '{userID}'
        """
    #连接数据库并执行查询，返回的是元组列表[()]
    result = access_DB(query)
    return result


#混合查询官方+用户
#查找所有方法
def get_all_MET(userID):
    #新逻辑
    query = """SELECT DISTINCT Method FROM param_data;"""
    result = access_DB(query)
    result0 = [item[0] for item in result] #元组列表变为列表 列表推导式 
    result1 = list(set(result0))  #去重
    
    #加入用户的相关参数
    query_user = f"""SELECT DISTINCT Method FROM USER_PARAM_T WHERE USER_ID={userID};"""
    result_user = access_DB(query_user)
    result_user0=[item[0] for item in result_user]
    result1.extend(result_user0)
    return result1

#查找所有材料
def get_all_MAT(userID):
    #新逻辑
    query = """SELECT Material FROM param_data;"""
    result = access_DB(query)
    result0 = [item[0] for item in result] #元组列表变为列表 列表推导式 
    result1 = list(set(result0))  #去重
    
    #加入用户的相关参数
    query_user = f"""SELECT DISTINCT Material FROM USER_PARAM_T WHERE USER_ID={userID};"""
    result_user = access_DB(query_user)
    result_user0=[item[0] for item in result_user]
    result1.extend(result_user0)
    return result1

