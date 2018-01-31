# coding: utf-8


from tornado.web import Application
from tornado.ioloop import IOLoop

import handlers


def test():
    from controller import biz
    print biz.gen_room('666', {
        "question": [
            {
                "content": "xxx",
                "choice": ["0", "1", "2"],
                "answer": 2
            },
            {
                "content": "xxx1",
                "choice": ["0", "1", "2"],
                "answer": 1
            },
            {
                "content": "xxx2",
                "choice": ["0", "1", "2"],
                "answer": 0
            }
        ],
        "reward": 100
    })


def main():
    test()
    app = Application(handlers=[
        (r'/qqq/create', handlers.CreateRoomHandler),
        (r'/qqq/user', handlers.GetUserOpenidHandler),
        (r'/qqq/ws', handlers.WsHandler)
    ])
    app.listen(8999, xheaders=True)
    IOLoop.current().start()


if __name__ == '__main__':
    main()
