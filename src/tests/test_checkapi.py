import unittest
import os
import Queue
from api.check_api import CheckApi


class CommandMock():


    def __init__(self, string):
        self.command = string


class CheckApiTest(unittest.TestCase):


    def setUp(self):
        self.TESTPATH = '/tmp/test_edbc.cmd'

    def testCreateCommand(self):
        receptor = CheckApi()
        receptor.setup("test", {
            "commandCls" : CommandMock
        })
        cmd = receptor.create_command("test=test123")
        self.assertTrue(isinstance(cmd, CommandMock))


    def testReceiveMessage(self):
        receptor = CheckApi()
        receptor.setup("test", {
            "path" :  self.TESTPATH,
            "commandCls" : CommandMock
        })

        queue = Queue.Queue()
        receptor.start(queue)








