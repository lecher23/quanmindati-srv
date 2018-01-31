# coding: utf-8

import json


def closed_message():
    return '{"code": 1}'


def status_trans_message(data):
    return json.dumps({"code": 2, "data": data}, ensure_ascii=False)


def snapshot_message(snapshot):
    return json.dumps({'code': 3, 'data': snapshot}, ensure_ascii=False)


def success_response(data=None):
    return json.dumps({"code": 0, "data": data}, ensure_ascii=False) if data else '{"code": 0}'


def failed_response(reason):
    return '{"code": 1, "msg": "%s"}' % reason
