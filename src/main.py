# coding: utf-8


from tornado.web import Application
from tornado.ioloop import IOLoop

import handlers


def main():
    app = Application(handlers=[
        (r'/qqq/create', handlers.CreateRoomHandler),
        (r'/qqq/user', handlers.GetUserOpenidHandler),
        (r'/qqq/ws', handlers.WebSocketHandler)
    ])
    app.listen(8999, xheaders=True)
    IOLoop.current().start()


if __name__ == '__main__':
    main()
