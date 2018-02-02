# coding: utf-8

import sys
import copy
import logging
from tornado.web import Application
from tornado.ioloop import IOLoop

import handlers


def test():
    from controller import biz
    print biz.gen_room('666', {
        "question": [
            {
                "content": "问题1",
                "choice": ["错误", "错误", "正确"],
                "answer": 2
            },
            {
                "content": "问题2",
                "choice": ["错误", "正确", "错误"],
                "answer": 1
            },
            {
                "content": "问题3",
                "choice": ["正确", "错误", "错误"],
                "answer": 0
            }
        ],
        "reward": 100
    })


def main():
    test()
    from tornado.options import define, options

    define("port", 8999, help="Server listen port", type=int)

    default_params = {
        '--log-to-stderr': 'true',
        '--log_file_prefix': 'logs/server.log',
        '--log_rotate_mode': 'time',
        '--logging': 'info',
        '--log_file_num_backups': '7'
    }
    extra_params = copy.copy(default_params)
    for item in sys.argv:
        for p in default_params:
            if item.startswith(p):
                extra_params.pop(p)
    sys.argv += ['%s=%s' % (k, v) for k, v in extra_params.items()]
    options.parse_command_line()

    app = Application(handlers=[
        (r'/qqq/create', handlers.CreateRoomHandler),
        (r'/qqq/user', handlers.GetUserOpenidHandler),
        (r'/qqq/ws', handlers.WsHandler)
    ])
    app.listen(options.port, xheaders=True)
    logging.info('Listen to port: %s', options.port)

    IOLoop.current().start()


if __name__ == '__main__':
    main()
