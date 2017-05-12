# This file is part of eventmq.
#
# eventmq is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option)
# any later version.
#
# eventmq is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with eventmq.  If not, see <http://www.gnu.org/licenses/>.
import random
import unittest

import mock

from .. import constants
from .. import exceptions
from ..utils import classes, messages


class EMQPServiceTestCase(unittest.TestCase):

    # pretend to be an emq socket
    frontend = 'some-frontend-socket'

    def get_worker(self):
        """return an EMQPService mimicking a worker"""
        obj = classes.EMQPService()
        obj.SERVICE_TYPE = constants.CLIENT_TYPE.worker
        obj.frontend = self.frontend
        obj._meta = {
            'last_sent_heartbeat': 0
        }

        return obj

    def get_scheduler(self):
        """return an EMQPService mimicking a scheduler"""
        obj = classes.EMQPService()
        obj.SERVICE_TYPE = constants.CLIENT_TYPE.scheduler
        obj.frontend = self.frontend
        obj._meta = {
            'last_sent_heartbeat': 0
        }

        return obj

    @mock.patch('eventmq.utils.classes.sendmsg')
    def test_send_inform_return_msgid(self, sendmsg_mock):
        obj = self.get_worker()
        sendmsg_mock.return_value = 'some-msgid'

        retval = obj.send_inform(queues=[(10, 'default'), ])

        self.assertEqual(retval, sendmsg_mock.return_value)

    @mock.patch('eventmq.utils.classes.sendmsg')
    def test_send_inform_empty_queue_name(self, sendmsg_mock):
        obj = self.get_worker()

        obj.send_inform()

        sendmsg_mock.assert_called_with(
            self.frontend, 'INFORM',
            ['', constants.CLIENT_TYPE.worker])

    @mock.patch('eventmq.utils.classes.sendmsg')
    def test_send_inform_scheduler(self, sendmsg_mock):
        obj = self.get_scheduler()

        obj.send_inform(queues="this shouldn't matter")

        sendmsg_mock.assert_called_with(
            self.frontend, 'INFORM',
            ['', constants.CLIENT_TYPE.scheduler]
        )

    @mock.patch('eventmq.utils.classes.sendmsg')
    def test_send_inform_specified_valid_queues(self, sendmsg_mock):
        obj = self.get_worker()

        obj.send_inform(queues=([10, 'push'], [7, 'email'],
                                [3, 'default']))
        sendmsg_mock.asert_called_with(
            'some-frontend-socket', 'INFORM',
            ['[10, "push"],[7, "email"],[3, "default"]',
             constants.CLIENT_TYPE.worker]
        )

    @mock.patch('eventmq.utils.classes.sendmsg')
    def test_send_inform_update_last_sent_heartbeat(self, sendmsg_mock):
        obj = self.get_worker()

        obj.send_inform(queues=(['', constants.CLIENT_TYPE.worker]))

        self.assertGreater(obj._meta['last_sent_heartbeat'], 0)


class TestCase(unittest.TestCase):
    def test_generate_msgid(self):
        msgid = messages.generate_msgid()

        self.assertEqual(type(msgid), str)

    def test_parse_message(self):
        emq_headers = ('myid', '', 'protoversion', 'command', 'msgid')
        emq_frame_singlemsg = emq_headers + ('my message',)
        emq_frame_manymsg = emq_headers + ('many', 'parts')
        emq_frame_nomsg = emq_headers

        singlemsg = messages.parse_router_message(emq_frame_singlemsg)
        manymsg = messages.parse_router_message(emq_frame_manymsg)
        nomsg = messages.parse_router_message(emq_frame_nomsg)

        self.assertEqual(singlemsg[0], emq_frame_singlemsg[0])
        self.assertEqual(singlemsg[1], emq_frame_singlemsg[3])
        self.assertEqual(singlemsg[2], emq_frame_singlemsg[4])
        self.assertEqual(singlemsg[3], (emq_frame_singlemsg[5],))

        self.assertEqual(manymsg[0], emq_frame_manymsg[0])
        self.assertEqual(manymsg[1], emq_frame_manymsg[3])
        self.assertEqual(manymsg[2], emq_frame_manymsg[4])
        self.assertEqual(manymsg[3], emq_frame_manymsg[5:])

        self.assertEqual(nomsg[0], emq_frame_nomsg[0])
        self.assertEqual(nomsg[1], emq_frame_nomsg[3])
        self.assertEqual(nomsg[2], emq_frame_nomsg[4])
        self.assertEqual(nomsg[3], ())

        broken_message = ('dlkajfs', 'lkasdjf')
        with self.assertRaises(exceptions.InvalidMessageError):
            messages.parse_router_message(broken_message)

    @unittest.skip
    def test_parse_router_message(self):
        ['aef451a0-5cef-4f03-818a-221061c8ab68', '', 'eMQP/1.0', 'INFORM',
         '5caeb5fd-15d4-4b08-89e8-4e536672eef3', 'default', 'worker']

    def test_emqDeque(self):

        full = random.randint(2, 100)
        pfull = random.randint(1, full-1)

        q = classes.EMQdeque(full=full,
                             pfull=pfull)

        # P Fill
        for i in range(0, pfull):
            q.append(i)
        self.assertTrue(q.is_pfull())
        self.assertFalse(q.is_full())

        while len(q) > 0:
            q.pop()

        # Fill
        for i in range(0, full*4):
            q.append(i)

        self.assertTrue(q.is_full())
        self.assertTrue(q.is_pfull())

        # Is iterable?
        for i in q:
            assert True

        # Check overflow
        self.assertEqual(len(q), full)

        # Remove everything we tried to insert
        for i in range(0, full*4):
            if i in q:
                q.remove(i)
            elif len(q) > 0:
                q.popleft()

        # Assert empty
        self.assertEqual(len(q), 0)
        self.assertTrue(q.is_empty())

        for i in q:
            q.remove(i)

        self.assertEqual(len(q), 0)
