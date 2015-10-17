#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'wuyuxi'

from base.smartsql import Table as T, Field as F, QuerySet as QS
from base import constant as const
from base import util


def get_account_by_username(db, username):
    return QS(db).table(T.account).where(
        (F.username == username) & (F.status == const.ACCOUNT_STATUS.NORMAL)
    ).select_one()


def get_account_by_id(db, account_id):
    return QS(db).table(T.account).where(
        (F.id == account_id) & (F.status == const.ACCOUNT_STATUS.NORMAL)
    ).select_one()


def get_devices_by_account_id(db, account_id):
    return QS(db).table(T.device).where(
        (F.account_id == account_id) & (F.status == const.DEVICE_STATUS.NORMAL)
    ).select()


def update_device_by_account_id(db, account_id, device_id):
    return QS(db).table(T.device).where(
        (F.account_id == account_id) & (F.id == device_id) & (F.status == const.DEVICE_STATUS.NORMAL)
    ).select_one(for_update=True)


def update_task_by_account_id(db, account_id, task_id):
    return QS(db).table(T.task).where(
        (F.account_id == account_id) & (F.status == const.TASK_STATUS.NORMAL) & (F.id == task_id)
    ).select_one(for_update=True)


def update_src_by_account_id(db, account_id, src_id):
    return QS(db).table(T.src).where(
        (F.account_id == account_id) & (F.status == const.TASK_STATUS.NORMAL) & (F.id == src_id)
    ).select_one(for_update=True)


def get_device_by_account_id(db, account_id, device_id):
    return QS(db).table(T.device).where(
        (F.account_id == account_id) & (F.id == device_id) & (F.status == const.DEVICE_STATUS.NORMAL)
    ).select_one()


def get_tasks_by_account_id(db, account_id):
    return QS(db).table(T.task).where(
        (F.account_id == account_id) & (F.status == const.TASK_STATUS.NORMAL)
    ).order_by(F.create_time, desc=True).select()


def get_srcs_by_account_id(db, account_id):
    return QS(db).table(T.src).where(
        (F.account_id == account_id) & (F.status == const.SRC_STATUS.NORMAL)
    ).order_by(F.create_time, desc=True).select()


def register(db, username, password):
    hash_pwd = util.hash_password(password, username)

    user_id = QS(db).table(T.account).insert({
        "username": username,
        "password": hash_pwd,
        "name": None,
        "status": const.ACCOUNT_STATUS.NORMAL,
        "role_id": const.ROLE.NORMAL_ACCOUNT,
    })
    msg = {
        "user_id": user_id,
        "role_id": const.ROLE.NORMAL_ACCOUNT,
        "username": username,
    }
    return True, msg

