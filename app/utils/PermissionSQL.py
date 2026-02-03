#1212增加
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional
import mysql.connector
from mysql.connector.connection import MySQLConnection
from app.config import config

# ---------------------------
# 连接配置：本地端口连接（localhost:3306）
# ---------------------------
user = config.MYSQL_USER
password = config.MYSQL_PASSWORD

class PermissionDB:

    def _get_conn(self) -> MySQLConnection:
        # 本地端口连接（host+port）
        return mysql.connector.connect(
            host= "localhost",
            port=3306,
            user=user,
            password=password ,
            database="welding",
            autocommit=False,
        )
    # ---------------------------
    # 增 （Create）
    # ---------------------------
    
    def add_permission_if_not_exists(self, uid: str, machine: str) -> int:
        """
        若 (uid, machine) 已存在则不插入，返回 0；
        不存在则插入，返回 1。
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM PERMISSION WHERE UID = %s AND MACHINE = %s LIMIT 1;",
                (uid, machine),
            )
            if cursor.fetchone() is not None:
                return 0

            cursor.execute(
                "INSERT INTO PERMISSION (UID, MACHINE) VALUES (%s, %s);",
                (uid, machine),
            )
            conn.commit()
            return cursor.rowcount
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()
    # ---------------------------
    # 查 (Read)
    # ---------------------------
    def get_all(self) -> List[Tuple[str, str]]:
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT UID, MACHINE FROM PERMISSION;")
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    def get_by_uid(self, uid: str) -> List[str]:
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT MACHINE FROM PERMISSION WHERE UID = %s;",
                (uid,),
            )
            return [row[0] for row in cursor.fetchall()]
        finally:
            cursor.close()
            conn.close()
    
    def get_by_machine(self, machine: str) -> List[str]:
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT UID FROM PERMISSION WHERE MACHINE = %s;",
                (machine,),
            )
            return [row[0] for row in cursor.fetchall()]
        finally:
            cursor.close()
            conn.close()

    def has_permission(self, uid: str, machine: str) -> bool:
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM PERMISSION WHERE UID = %s AND MACHINE = %s LIMIT 1;",
                (uid, machine),
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()
            conn.close()

    # ---------------------------
    # 改 (Update)
    # ---------------------------
    def update_machine(self, uid: str, old_machine: str, new_machine: str) -> int:
        """
        将某个 uid 的 old_machine 更新为 new_machine
        返回：受影响行数（0 表示没找到匹配记录）
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE PERMISSION
                SET MACHINE = %s
                WHERE UID = %s AND MACHINE = %s;
                """,
                (new_machine, uid, old_machine),
            )
            conn.commit()
            return cursor.rowcount
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    # ---------------------------
    # 删 (Delete)
    # ---------------------------
    def delete_one(self, uid: str, machine: str) -> int:
        """
        删除一条 (uid, machine)
        返回：删除行数
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM PERMISSION WHERE UID = %s AND MACHINE = %s;",
                (uid, machine),
            )
            conn.commit()
            return cursor.rowcount
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def delete_by_uid(self, uid: str) -> int:
        """
        删除某个 uid 的所有权限
        返回：删除行数
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM PERMISSION WHERE UID = %s;",
                (uid,),
            )
            conn.commit()
            return cursor.rowcount
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()
            
    def delete_by_machine(self, machine: str) -> int:
        """
        删除某个machine 的所有权限
        返回：删除行数
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM PERMISSION WHERE MACHINE = %s;",
                (machine,),
            )
            conn.commit()
            return cursor.rowcount
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()
            
db = PermissionDB()
