from typing import Dict, Any
from fastapi import APIRouter, Query

from app.services.PermissionService import (
    SERVICE_add_permission_if_not_exists,
    SERVICE_get_all,
    SERVICE_get_by_uid,
    SERVICE_get_by_machine,
    SERVICE_has_permission,
    SERVICE_update_machine,
    SERVICE_delete_one,
    SERVICE_delete_by_uid,
    SERVICE_delete_by_machine,
)

router = APIRouter(prefix="/permission", tags=["permission"])

#1213修改接口为get
# -------------------------
# 接口：增（改为 GET + Query）
# -------------------------
@router.get("/add_permission_if_not_exists", response_model=dict)
def INTERFACE_add_permission_if_not_exists(
    userID: str = Query(..., description="User ID"),
    machine: str = Query(..., description="Machine identifier"),
) -> Dict[str, Any]:
    return SERVICE_add_permission_if_not_exists(userID, machine)


# -------------------------
# 接口：查（GET）
# -------------------------
@router.get("/get_all", response_model=dict)
def INTERFACE_get_all() -> Dict[str, Any]:
    return SERVICE_get_all()


@router.get("/get_by_uid", response_model=dict)
def INTERFACE_get_by_uid(
    userID: str = Query(..., description="User ID"),
) -> Dict[str, Any]:
    return SERVICE_get_by_uid(userID)


@router.get("/get_by_machine", response_model=dict)
def INTERFACE_get_by_machine(
    machine: str = Query(..., description="Machine identifier"),
) -> Dict[str, Any]:
    return SERVICE_get_by_machine(machine)


@router.get("/has_permission", response_model=dict)
def INTERFACE_has_permission(
    userID: str = Query(..., description="User ID"),
    machine: str = Query(..., description="Machine identifier"),
) -> Dict[str, Any]:
    return SERVICE_has_permission(userID, machine)


# -------------------------
# 接口：改（改为 GET + Query）
# -------------------------
@router.get("/update_machine", response_model=dict)
def INTERFACE_update_machine(
    userID: str = Query(..., description="User ID"),
    old_machine: str = Query(..., description="Old machine identifier"),
    new_machine: str = Query(..., description="New machine identifier"),
) -> Dict[str, Any]:
    return SERVICE_update_machine(userID, old_machine, new_machine)


# -------------------------
# 接口：删（改为 GET + Query）
# -------------------------
@router.get("/delete_one", response_model=dict)
def INTERFACE_delete_one(
    userID: str = Query(..., description="User ID"),
    machine: str = Query(..., description="Machine identifier"),
) -> Dict[str, Any]:
    return SERVICE_delete_one(userID, machine)


@router.get("/delete_by_uid", response_model=dict)
def INTERFACE_delete_by_uid(
    userID: str = Query(..., description="User ID"),
) -> Dict[str, Any]:
    return SERVICE_delete_by_uid(userID)


@router.get("/delete_by_machine", response_model=dict)
def INTERFACE_delete_by_machine(
    machine: str = Query(..., description="Machine identifier"),
) -> Dict[str, Any]:
    return SERVICE_delete_by_machine(machine)



#废弃，没法兼容中间件
# from typing import Optional, Dict, Any
# from fastapi import APIRouter
# from pydantic import BaseModel

# from app.services.PermissionService import (
#     SERVICE_add_permission_if_not_exists,
#     SERVICE_get_all,
#     SERVICE_get_by_uid,
#     SERVICE_get_by_machine,
#     SERVICE_has_permission,
#     SERVICE_update_machine,
#     SERVICE_delete_one,
#     SERVICE_delete_by_uid,
#     SERVICE_delete_by_machine,
# )

# router = APIRouter(prefix="/permission", tags=["permission"])


# # -------------------------
# # 请求体模型（JSON Body）
# # -------------------------
# class AddPermissionReq(BaseModel):
#     uid: str
#     machine: str


# class UIDReq(BaseModel):
#     uid: str


# class MachineReq(BaseModel):
#     machine: str


# class HasPermissionReq(BaseModel):
#     uid: str
#     machine: str


# class UpdateMachineReq(BaseModel):
#     uid: str
#     old_machine: str
#     new_machine: str


# class DeleteOneReq(BaseModel):
#     uid: str
#     machine: str

# # -------------------------
# # 接口：增
# # -------------------------
# @router.post("/add_permission_if_not_exists", response_model=dict)
# def INTERFACE_add_permission_if_not_exists(req: AddPermissionReq):
#     return SERVICE_add_permission_if_not_exists(req.uid, req.machine)

# # -------------------------
# # 接口：查
# # -------------------------
# @router.get("/get_all", response_model=dict)
# def INTERFACE_get_all():
#     return SERVICE_get_all()

# @router.post("/get_by_uid", response_model=dict)
# def INTERFACE_get_by_uid(req: UIDReq):
#     return SERVICE_get_by_uid(req.uid)

# @router.post("/get_by_machine", response_model=dict)
# def INTERFACE_get_by_machine(req: MachineReq):
#     return SERVICE_get_by_machine(req.machine)

# @router.post("/has_permission", response_model=dict)
# def INTERFACE_has_permission(req: HasPermissionReq):
#     return SERVICE_has_permission(req.uid, req.machine)

# # -------------------------
# # 接口：改
# # -------------------------
# @router.put("/update_machine", response_model=dict)
# def INTERFACE_update_machine(req: UpdateMachineReq):
#     return SERVICE_update_machine(req.uid, req.old_machine, req.new_machine)


# # -------------------------
# # 接口：删
# # -------------------------
# @router.delete("/delete_one", response_model=dict)
# def INTERFACE_delete_one(req: DeleteOneReq):
#     return SERVICE_delete_one(req.uid, req.machine)


# @router.delete("/delete_by_uid", response_model=dict)
# def INTERFACE_delete_by_uid(req: UIDReq):
#     return SERVICE_delete_by_uid(req.uid)


# @router.delete("/delete_by_machine", response_model=dict)
# def INTERFACE_delete_by_machine(req: MachineReq):
#     return SERVICE_delete_by_machine(req.machine)
