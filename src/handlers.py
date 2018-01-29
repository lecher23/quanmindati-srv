# coding: utf-8

import json
import logging
import tornado.gen
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
        self.write('{"code": 0, "openid": %s}' % data if data else '{"code": 500, "msg": "get failed."}')


class WsHandler(WebSocketHandler):
    def check_origin(self, origin):
        return True

    def on_close(self):
        pass

    def open(self):
        pass
