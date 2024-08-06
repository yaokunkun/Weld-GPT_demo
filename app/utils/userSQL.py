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

def get_all_userID():
    query = """SELECT UserID FROM userinfo;"""
    result = access_DB(query)
    if result is not None and len(result) > 0:
        new_result = [(int(ret[0]),) for ret in result]
    else:
        new_result = [(0,)]
    return new_result

def select_SQL_by_userID(userID):
    query = """SELECT * FROM userinfo
    WHERE UserID = {};""".format(userID)
    return access_DB(query)

def insert_SQL(user):
    query = """INSERT INTO userinfo (UserID, UserName, Password, PhoneNumber, UserRole)
VALUES ({}, '{}', '{}', '{}', '{}')
""".format(user.UserID, user.UserName, user.Password, user.PhoneNumber, user.UserRole)
    result = access_DB(query)
    return result

def update_SQL(user):
    query = """UPDATE  userinfo
    SET UserName = '{}',
    Password = '{}',
    PhoneNumber = '{}',
    UserRole = '{}'
    WHERE UserID = {}
    """.format(user.UserName, user.Password, user.PhoneNumber, user.UserRole, user.UserID)
    result = access_DB(query)
    return result

def login_by_userName(UserName, Password):
    query = """SELECT UserID, Password FROM userinfo
        WHERE UserName = '{}';""".format(UserName)
    result = access_DB(query)
    return result

def login_by_PhoneNumber(PhoneNumber, Password):
    query = """SELECT UserID, Password FROM userinfo
        WHERE PhoneNumber = '{}';""".format(PhoneNumber)
    result = access_DB(query)
    return result