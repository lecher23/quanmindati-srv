# coding: utf-8

import json
import logging
import tornado.gen
import message
from controller import biz
from tornado.web import RequestHandler, asynchronous
from tornado.websocket import WebSocketHandler
from tornado.httpclient import AsyncHTTPClient

appid = ''
secret = ''
wx_url = 'https://api.weixin.qq.com/sns/jscode2session'


class GetUserOpenidHandler(RequestHandler):
    @asynchronous
    @tornado.gen.coroutine
    def get(self):
        code = self.get_argument('code')
        url = '{}?appid={}&secret={}&js_code={}&grant_type=authorization_code'.format(wx_url, appid, secret, code)
        data = None
        try:
            response = yield AsyncHTTPClient().fetch(url)
            if not response.error:
                obj = json.loads(response.body)
                if 'openid' in obj:
                    data = obj['openid']
                else:
                    logging.warning('get user openid failed with code: %s, response: %s', code, response.body)
        except:
            logging.warning('get user openid failed with code: %s', code)
        self.write(message.success_response(data) if data else message.failed_response('get openid failed'))


class CreateRoomHandler(RequestHandler):
    def get(self):
        user_id = self.get_argument('u')
        data = self.get_argument('q')
        room_id, reason = biz.gen_room(user_id, data)
        if room_id:
            self.write(message.success_response(room_id))
        else:
            self.write(message.failed_response(reason))


class WsHandler(WebSocketHandler):
    def initialize(self):
        self.room_id = None

    def check_origin(self, origin):
        return True

    def force_close(self):
        self.close()

    def on_close(self):
        if self.room_id:
            biz.remove(self.current_user, self.room_id)

    def open(self):
        self.current_user = self.get_argument('u')
        self.room_id = self.get_argument('r')
        if biz.register(self.current_user, self.room_id, self.write_message):
            snp = biz.room_snapshot(self.current_user, self.room_id)
            self.write_message(message.snapshot_message(snp))
        else:
            self.close(4100, 'room not exist.')

    def on_message(self, msg):
        msg_obj = json.loads(msg)
        if msg_obj['t'] == 1:
            # 答题
            pass
        elif msg_obj['t'] == 2:
            # 开启房间
            success, reason = biz.start_room(self.current_user, self.room_id)
            self.write_message(message.success_response() if success else message.failed_response(reason))
        elif msg_obj['t'] == 3:
            # 重启房间
            pass
        elif msg_obj['t'] == 4:
            # 群体复活
            pass
