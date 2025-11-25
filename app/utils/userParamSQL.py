import mysql.connector
from app.config import config

user = config.MYSQL_USER
password = config.MYSQL_PASSWORD

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

def select_SQL(MET, MAT, THI, userID):
    query = """SELECT DataIndex, WireDiameter
FROM paramsdatatable
WHERE (WeldingMethod, WeldingMaterial, WireDiameter, ParamIndex) IN (
SELECT WeldingMethod, WeldingMaterial, WireDiameter, ParamIndex
                   FROM paramsdatatable AS pt, userparamsdatatable AS upt
                   WHERE pt.WeldingMethod = '{}'
                   AND pt.WeldingMaterial = '{}'
                   AND pt.ParamName = 'Guideline value for material'
                   AND pt.ParamValue = '-100'
                   AND pt.DataIndex = upt.DataIndex
                   AND upt.UserID = '{}'
                   AND ROUND(upt.DataValue, 1) = {}
               );
    """.format(MET, MAT, userID, THI)
    result = access_DB(query)
    result_dict = {}
    for dataIndex, diameter in result:
        if f"WireDiameter:{diameter}" not in result_dict:
            result_dict[f"WireDiameter:{diameter}"] = []
        result_dict[f"WireDiameter:{diameter}"].append(dataIndex)

    return result_dict

def select_by_ID(dataIndex, userID):
    query = """SELECT DataValue
                            FROM userparamsdatatable
                            WHERE DataIndex = {}
                            AND UserID = {};""".format(dataIndex, userID)
    result = access_DB(query)
    return result

def get_all_userDataIndex():
    query = """SELECT UserDataIndex FROM userparamsdatatable;"""
    return access_DB(query)

def insert_SQL(userParams):
    query = """INSERT INTO userparamsdatatable (UserDataIndex, DataIndex, UserID, DataValue)
    VALUES ({}, {}, {}, {})
    """.format(userParams.UserDataIndex, userParams.DataIndex, userParams.UserID, userParams.DataValue)
    result = access_DB(query)
    return result

def update_SQL(userParams):
    query = """UPDATE userparamsdatatable
    SET DataValue = {}
    WHERE DataIndex = {} AND UserID = {};
    """.format(userParams.DataValue, userParams.DataIndex, userParams.UserID)
    result = access_DB(query)
    return result

def get_userDataIndex(userParams):
    query="""SELECT UserDataIndex
    FROM userparamsdatatable
    WHERE DataIndex = {} AND UserID = {};
    """.format(userParams.DataIndex, userParams.UserID)
    result = access_DB(query)
    return result

def get_value_from_dataIndex(userID, dataIndex):
    query = """SELECT DataValue
        FROM userparamsdatatable
        WHERE DataIndex = {} AND UserID = {};
        """.format(dataIndex, userID)
    result = access_DB(query)
    return result