# coding: utf-8

import json
import logging
import tornado.gen
import message
from controller import biz
from data import sys_users
from tornado.web import RequestHandler, asynchronous
from tornado.websocket import WebSocketHandler
from tornado.httpclient import AsyncHTTPClient

wx_url = 'https://api.weixin.qq.com/sns/jscode2session'


class RegisterUserHandler(RequestHandler):
    def post(self):
        data = json.loads(self.request.body)
        user_id = data['id']
        user_name = data['name']
        user_avatar = data['avatar']
        sys_users.register(user_id, user_name, user_avatar)
        self.write(message.success_response())


class GetUserOpenidHandler(RequestHandler):
    @asynchronous
    @tornado.gen.coroutine
    def get(self):
        code = self.get_argument('code')
        url = '{}?appid={}&secret={}&js_code={}&grant_type=authorization_code'.format(
            wx_url, self.settings['appid'], self.settings['secret'], code)
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
    def post(self):
        logging.info(self.request.body)
        obj = json.loads(self.request.body)
        user_id = obj['u']
        data = obj['d']
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
        if biz.register(self.current_user, self.room_id, self):
            snp = biz.room_snapshot(self.current_user, self.room_id)
            self.write_message(message.snapshot_message(snp))
        else:
            logging.info('room %s not exist.', self.room_id)
            self.close(4100, 'room not exist.')

    def on_message(self, msg):
        msg_obj = json.loads(msg)
        success, reason = False, 'invalid message'
        if msg_obj['t'] == 1:
            # 答题
            logging.info('user %s answer room %s question', self.current_user, self.room_id)
            success, reason = biz.answer_question(self.current_user, self.room_id, msg_obj['d'])
        elif msg_obj['t'] == 2:
            # 开启房间
            logging.info('user %s start room %s', self.current_user, self.room_id)
            success, reason = biz.start_room(self.current_user, self.room_id)
        elif msg_obj['t'] == 3:
            # 重启房间
            logging.info('user %s restart room %s', self.current_user, self.room_id)
            success, reason = biz.reset_room(self.current_user, self.room_id)
        elif msg_obj['t'] == 4:
            # 群体复活
            pass
        self.write_message(message.success_response() if success else message.failed_response(reason))
