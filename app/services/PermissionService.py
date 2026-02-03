from app.utils.PermissionSQL import db
import mysql.connector


# 增 （Create）
def SERVICE_add_permission_if_not_exists(uid: str, machine: str):
    try:
        result = db.add_permission_if_not_exists(uid, machine)
        if result == 0:
            return {"info": "数据已存在", "inserted": 0}
        else:
            # result 通常是 1（插入1行）
            return {"info": "数据添加成功", "inserted": result}
    except mysql.connector.Error:
        print("数据库连接错误")
        return {"info": "数据库连接异常"}
    except Exception as e:
        print("数据库层未知错误:", e)
        return {"info": "数据库未知原因增加失败"}


# 查：全表
def SERVICE_get_all():
    try:
        result = db.get_all()
        if result:
            return {"info": "全数据库有数据！", "result": result}
        else:
            return {"info": "无数据", "result": []}
    except mysql.connector.Error:
        print("数据库连接错误")
        return {"info": "数据库连接异常"}
    except Exception as e:
        print("数据库层未知错误:", e)
        return {"info": "数据库未知原因查询失败"}


# 查：按 UID
def SERVICE_get_by_uid(uid: str):
    try:
        result = db.get_by_uid(uid)  # List[str]
        if result:
            return {"info": "根据你提供的UID数据查到数据!", "uid": uid, "machines": result}
        else:
            return {"info": "你提供的UID下无数据", "uid": uid, "machines": []}
    except mysql.connector.Error:
        print("数据库连接错误")
        return {"info": "数据库连接异常"}
    except Exception as e:
        print("数据库层未知错误:", e)
        return {"info": "数据库未知原因查询失败"}


# 查：按 MACHINE
def SERVICE_get_by_machine(machine: str):
    try:
        result = db.get_by_machine(machine)  # List[str]
        if result:
            return {"info": "根据你提供的MACHINE查到数据!", "machine": machine, "uids": result}
        else:
            return {"info": "你提供的MACHINE下无数据", "machine": machine, "uids": []}
    except mysql.connector.Error:
        print("数据库连接错误")
        return {"info": "数据库连接异常"}
    except Exception as e:
        print("数据库层未知错误:", e)
        return {"info": "数据库未知原因查询失败"}


# 查：是否有权限
def SERVICE_has_permission(uid: str, machine: str):
    try:
        ok = db.has_permission(uid, machine)  # bool
        return {"info": "查询成功", "uid": uid, "machine": machine, "has_permission": ok}
    except mysql.connector.Error:
        print("数据库连接错误")
        return {"info": "数据库连接异常"}
    except Exception as e:
        print("数据库层未知错误:", e)
        return {"info": "数据库未知原因查询失败"}


# 改：更新 machine（同一 uid 下 old_machine -> new_machine）
def SERVICE_update_machine(uid: str, old_machine: str, new_machine: str):
    try:
        affected = db.update_machine(uid, old_machine, new_machine)  # int
        if affected == 0:
            return {
                "info": "未找到匹配记录，未更新",
                "uid": uid,
                "old_machine": old_machine,
                "new_machine": new_machine,
                "updated": 0,
            }
        return {
            "info": "更新成功",
            "uid": uid,
            "old_machine": old_machine,
            "new_machine": new_machine,
            "updated": affected,
        }
    except mysql.connector.Error:
        print("数据库连接错误")
        return {"info": "数据库连接异常"}
    except Exception as e:
        print("数据库层未知错误:", e)
        return {"info": "数据库未知原因更新失败"}


# 删：删除一条 (uid, machine)
def SERVICE_delete_one(uid: str, machine: str):
    try:
        affected = db.delete_one(uid, machine)  # int
        if affected == 0:
            return {"info": "未找到匹配记录，未删除", "uid": uid, "machine": machine, "deleted": 0}
        return {"info": "删除成功", "uid": uid, "machine": machine, "deleted": affected}
    except mysql.connector.Error:
        print("数据库连接错误")
        return {"info": "数据库连接异常"}
    except Exception as e:
        print("数据库层未知错误:", e)
        return {"info": "数据库未知原因删除失败"}


# 删：按 UID 删除所有权限
def SERVICE_delete_by_uid(uid: str):
    try:
        affected = db.delete_by_uid(uid)  # int
        if affected == 0:
            return {"info": "该UID下无可删除数据", "uid": uid, "deleted": 0}
        return {"info": "删除成功", "uid": uid, "deleted": affected}
    except mysql.connector.Error:
        print("数据库连接错误")
        return {"info": "数据库连接异常"}
    except Exception as e:
        print("数据库层未知错误:", e)
        return {"info": "数据库未知原因删除失败"}


# 删：按 MACHINE 删除所有权限
def SERVICE_delete_by_machine(machine: str):
    try:
        affected = db.delete_by_machine(machine)  # int
        if affected == 0:
            return {"info": "该MACHINE下无可删除数据", "machine": machine, "deleted": 0}
        return {"info": "删除成功", "machine": machine, "deleted": affected}
    except mysql.connector.Error:
        print("数据库连接错误")
        return {"info": "数据库连接异常"}
    except Exception as e:
        print("数据库层未知错误:", e)
        return {"info": "数据库未知原因删除失败"}
