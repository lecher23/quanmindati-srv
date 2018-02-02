# coding: utf-8

import json
import time
import copy
import message
from collections import defaultdict
from tornado.ioloop import PeriodicCallback


class Question(object):
    def __init__(self, content):
        self.content = content
        self.options = {}
        self.answer_key = None
        self.time_limit = 10
        self.answer_detail = defaultdict(int)

    def reset(self):
        self.answer_detail = defaultdict(int)

    def add_option(self, key, val, is_answer=False):
        self.options[key] = val
        if is_answer:
            self.answer_key = key

    def increment_answer(self, key):
        self.answer_detail[key] += 1

    def answer_summary(self):
        return {
            'answer': self.answer_key,
            'detail': {k: v for k, v in self.answer_detail.iteritems()}
        }

    def dump(self):
        return {
            'content': self.content,
            'options': [{'val': val, 'idx': key} for key, val in self.options.iteritems()],
            'answerTime': self.time_limit
        }


st_WaitStart = 0
st_StartCountDown = 1
st_AnswerQuestion = 2
st_WaitingShowAnswer = 3
st_ShowAnswer = 4
st_ShowReward = 5
st_Closed = 6


class Room(object):
    def __init__(self, enter_code, man_code, close_callback):
        self.enter_code = enter_code
        self.man_code = man_code
        self.owner = None

        self.created_time = time.time()
        self.questions = []
        self.reward = 0  # 成功奖励
        self.status = 0  # 记录房间状态: 等待开始(0)/开始倒计时(1)/出题收集答案(2)/等待揭示结果(3)/答案结果展示(4)/奖金展示(5)/结束(6)
        self.status_conf = [1, 10, 10, 20, 10, 120, 10]  # 状态值
        # self.status_conf = [1, 1, 1, 1, 1, 1, 10]  # 状态值(测试用)
        self.question_idx = -1  # 当前问题序号
        self._snapshot = {'st': 0, 'duration': 0}  # 当前快照信息
        self.counter = 0

        self.user_count = 0  # 当前房间人数
        self.failed_users = set()  # 失败人数
        self.passed_users = set()  # 通过人数
        self.user_answers = defaultdict(list)

        self.close_handler = close_callback
        self.event_handler = None
        self.timer = PeriodicCallback(self.ticker, 1000)

    def revival_all(self):
        for u in self.failed_users:
            self.passed_users.add(u)
        return True

    def reset(self):
        for q in self.questions:
            q.reset()

        self.status = 0
        self.question_idx = -1  # 当前问题序号
        self._snapshot = {'st': 0, 'duration': 0}  # 当前快照信息
        self.counter = 0

        self.failed_users = set()  # 失败人数
        self.passed_users = set()  # 通过人数
        self.user_answers = defaultdict(list)

        self.timer.stop()
        return True

    @property
    def current_question(self):
        return self.questions[self.question_idx]

    def add_question(self, q):
        self.questions.append(q)

    def add_answer(self, user_id, question_idx, answer):
        if self.status != st_AnswerQuestion \
                or question_idx != self.question_idx \
                or (self.question_idx > 0 and user_id not in self.passed_users):
            return False
        self.user_answers[user_id].append(answer)
        cur_question = self.current_question
        cur_question.increment_answer(answer)
        if cur_question.answer_key != answer:
            self.passed_users.remove(user_id)
            self.failed_users.add(user_id)
        else:
            self.passed_users.add(user_id)
        return True

    def status_trans(self):
        self.status += 1
        if self.status == st_ShowReward and self.question_idx < len(self.questions) - 1:
            self.status = st_AnswerQuestion

        data = {'st': self.status, 'duration': self.status_conf[self.status]}

        if self.status == st_AnswerQuestion:
            self.question_idx += 1
            q = self.current_question
            self.status_conf[self.status] = q.time_limit  # 修改答题时间
            data['data'] = q.dump()
            self._snapshot = copy.copy(data)  # {"data": "question detail"}
        elif self.status == st_ShowAnswer:
            q = self.current_question
            data['data'] = q.answer_summary()
            self._snapshot['st'] = data['st']
            self._snapshot['duration'] = data['duration']
            self._snapshot['result'] = data['data']  # {"data": "question detail", "result": "answer detail"}
        elif self.status == st_ShowReward:
            data['data'] = {'reward': self.reward, 'passed': len(self.passed_users)}
            self._snapshot = copy.copy(data)
        else:
            self._snapshot['st'] = data['st']
            self._snapshot['duration'] = data['duration']
        self.event_handler(self.enter_code, message.status_trans_message(data), None)

        if self.status == st_Closed:
            # 调用结束通知
            self.timer.stop()
            self.close_handler(self)

    def ticker(self):
        self.counter += 1
        if self.counter > self.status_conf[self.status]:
            self.counter = 1
            self.status_trans()
        self._snapshot['counter'] = self.counter
        # print 'snapshot:', self._snapshot

    def start(self, callback):
        '''
        :param callback: 事件发生时的回调，function callback(room_id, message, target)
        :return:
        '''
        if not self.event_handler:
            self.event_handler = callback
            self.timer.start()
            return True
        return False

    def snapshot(self, user_id):
        '''当前状态, 当前进度, 题目快照'''
        answer_list = self.user_answers.get(user_id, [])
        answer_detail = {'enable': False, 'history': None}
        if user_id in self.passed_users or self.question_idx < 0:
            # 未答题，可以答题
            answer_detail['enable'] = True
        elif len(answer_list) == self.question_idx + 1:
            # 已答题
            answer_detail['history'] = answer_list[self.question_idx]
        ret = copy.copy(self._snapshot)
        return ret.update(answer_detail)

    def __repr__(self):
        data = {
            'reward': self.reward,
            'result': {
                'passed': list(self.passed_users),
                'failed': list(self.failed_users)
            },
            'detail': [
                {
                    'question': item.dump(),
                    'answer': item.answer_summary()
                }
                for item in self.questions
                ],
            'id': self.enter_code,
            'owner': self.owner
        }
        return json.dumps(data, ensure_ascii=False, indent=2)


def test():
    r = Room(2222, 666666, lambda _: tornado.ioloop.IOLoop.current().stop())
    for i in range(4):
        q = Question('问题 %s' % i)
        for j in range(3):
            q.add_option(j, '选项' + str(j), j == 2)
        r.add_question(q)
    print r
    import tornado.ioloop
    import sys
    r.start(lambda rid, ipt, tar: sys.stdout.write(str(ipt) + '\n'))
    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    test()
