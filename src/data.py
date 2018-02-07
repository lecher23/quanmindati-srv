# coding: utf-8

class Users(object):
    def __init__(self):
        self.users = {}

    def register(self, user_id, user_name, user_avatar):
        self.users[user_id] = (user_name, user_avatar)

    def query(self, user_id):
        n, a = self.users.get(user_id, ('未知', ''))
        return {'name': n, 'avatar': a}

sys_users = Users()
