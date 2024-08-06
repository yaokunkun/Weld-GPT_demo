import mysql.connector
from app_en.config import config

user = config.MYSQL_USER
password = config.MYSQL_PASSWORD
# user = "root"
# password = "SQMYSQL"

def entity2SQL(MET, MAT, THI):
    # （一）拼接SQL语句
    query = f"""SELECT ParamName, ParamValue, WireDiameter
FROM paramsdatatable
WHERE (WeldingProcessName, ParamIndex) IN (
SELECT WeldingProcessName, ParamIndex
                   FROM paramsdatatable
                   WHERE WeldingMethod = '{MET}'
                   AND WeldingMaterial = '{MAT}'
                   AND ParamName = 'Guideline value for material'
                   AND ParamValue = '{THI}'
               );"""

    #（二）连接数据库并执行查询
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

    except mysql.connector.Error as error:
        print("Error: ", error)

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

    # （三）组装查询结果为嵌套字典的格式，返回。
    result_dict = {}

    for param_name, param_value, diameter in result:
        if f"WireDiameter:{diameter}" not in result_dict:
            result_dict[f"WireDiameter:{diameter}"] = []
        # 对于每个参数和值，创建一个小字典并添加到列表中
        param_dict = {param_name: param_value}
        result_dict[f"WireDiameter:{diameter}"].append(param_dict)

    return result_dict

def get_all_MET():
    # （一）拼接SQL语句
    query = """SELECT DISTINCT WeldingMethod
FROM paramsdatatable;"""

    # （二）连接数据库并执行查询
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

    except mysql.connector.Error as error:
        print("Error: ", error)

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

    # （三）返回结果。
    result = [e[0] for e in result]
    return result

def get_all_MAT():
    # （一）拼接SQL语句
    query = """SELECT DISTINCT WeldingMaterial
FROM paramsdatatable;"""

    # （二）连接数据库并执行查询
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

    except mysql.connector.Error as error:
        print("Error: ", error)

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

    # （三）返回结果。
    result = [e[0] for e in result]
    return result

def get_all_THI(MET=None, MAT=None):
    # （一）拼接SQL语句
    # Basic query
    query = """
        SELECT DISTINCT ParamValue 
        FROM paramsdatatable 
        WHERE ParamName = 'Guideline value for material'
        """

    # If MET is provided, add it to the query
    if MET is not None:
        query += f"\nAND WeldingMethod = '{MET}'"

    # If MAT is provided, add it to the query
    if MAT is not None:
        query += f"\nAND WeldingMaterial = '{MAT}'"

    # Add the ORDER BY clause
    query += "\nORDER BY CAST(ParamValue AS DECIMAL(10, 2)) ASC;"

    # （二）连接数据库并执行查询
    try:
        # 连接到 MySQL 数据库
        connection = mysql.connector.connect(
            host="localhost",  # 数据库服务器地址
            port=3306,  # 数据库服务器端口
            user=user,  # 数据库用户名
            password=password,  # 数 据库密码
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

    except mysql.connector.Error as error:
        print("Error: ", error)

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

    # （三）返回结果。
    result = [e[0] for e in result]
    return result