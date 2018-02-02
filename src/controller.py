# coding: utf-8

import datetime
import random
import message
from collections import defaultdict
from tornado.ioloop import IOLoop
from room import Question, Room


class Controller(object):
    '''room_id is equal to enter_code'''

    def __init__(self):
        self.rooms = {}
        self.conns = defaultdict(dict)

    def gen_room(self, user_id, data):
        '''
        data:
        {
          "question": [
            {
              "content": "xxx",
              "choice": ["0", "1", "2"],
              "answer": 2
            }
          ],
          "reward": 100
        }
        :param user_id: wx user openid
        :param data: see below
        :return:

        '''
        for _ in range(0, 10):
            enter_code = str(random.randint(100000, 999999))
            if enter_code not in self.rooms:
                manager_code = random.randint(1000, 9999)
                room = Room(enter_code, manager_code, self.on_room_close)
                for item in data['question']:
                    q = Question(item['content'])
                    for i, choice in enumerate(item['choice']):
                        q.add_option(i, choice, i == item['answer'])
                    room.add_question(q)
                room.reward = data['reward']
                room.owner = user_id
                self.rooms[enter_code] = room
                return enter_code, None
        return None, 'too many rooms in server'

    def start_room(self, user_id, enter_code):
        room = self.rooms.get(enter_code, None)
        if room and room.owner == user_id:
            return room.start(self.on_room_message), 'room already started'
        return False, 'no private to start room'

    def reset_room(self, user_id, room_id):
        room = self.rooms.get(room_id, None)
        if not room:
            return False, 'room not exist'
        if room.owner != user_id:
            return False, 'no private'
        return room.reset(), 'reset failed'

    def answer_question(self, user_id, room_id, data):
        '''
        :param user_id:
        :param room_id:
        :param data: {"q": 1, "a": 2}
        :return:
        '''
        room = self.rooms.get(room_id, None)
        if not room:
            return False, 'room not exist'
        return room.add_answer(user_id, data['q'], data['a']), 'answer not allowed'

    def room_snapshot(self, user_id, room_id):
        room = self.rooms.get(room_id, None)
        if room:
            return room.snapshot(user_id)
        return None

    def on_room_message(self, room_id, msg, target=None):
        if not target:
            self.broadcast(room_id, msg)

    def on_room_close(self, room):
        room_conns = self.conns.pop(room.enter_code, {})
        il = IOLoop.current()
        for conn in room_conns.itervalues():
            # 广播通知客户端房间结束, 断开连接
            try:
                conn.write_message(message.closed_message())
                il.call_later(1, conn.close)
            except:
                pass
        dead_room = self.rooms.pop(room.enter_code)
        with open(datetime.datetime.now().strftime('%Y%m%d.%H%M%S.txt'), 'w') as f:
            f.write(str(dead_room))

    def register(self, user_id, room_id, conn):
        if room_id in self.rooms:
            self.conns[room_id][user_id] = conn
            return True
        return False

    def remove(self, user_id, room_id):
        self.conns[room_id].pop(user_id, None)

    def broadcast(self, room_id, msg):
        room_conns = self.conns.get(room_id, None)
        if room_conns:
            for conn in room_conns.itervalues():
                conn.write_message(msg)


biz = Controller()


def test():
    import sys
    ctrl = Controller()
    ctrl.register('user1', 100, lambda msg: sys.stdout.write(msg + '\n'))
    ctrl.broadcast(100, 'nihao')


if __name__ == '__main__':
    test()
