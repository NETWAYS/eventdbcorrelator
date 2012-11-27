import unittest
import os
import time
import logging

from processors import CommandProcessor
PIPE_LOCATION="/tmp/test.pipe"

class CommandProcessorTest(unittest.TestCase):
    
        
    def remove_temporary_file(self):
        try:
            os.unlink(PIPE_LOCATION)
        except:
            pass
        
    def test_unformatted_command_submit(self):
        try:
            f = open(PIPE_LOCATION,"w+")

            proc = CommandProcessor()
            proc.setup("test",{
                "pipe": PIPE_LOCATION,
                "format" : "Plain string"
            })
            event1 = {
                "message" : 'Testmessage',
                "priority" : 1,
                'anotherfield' : 5
            }
            proc.process(event1)
            f.seek(0)

            assert f.readline().endswith("Plain string\n")
        finally:
            self.remove_temporary_file()
            
    
    def test_formatted_command_submit(self):
        try:
            f = open(PIPE_LOCATION,"w+")

            proc = CommandProcessor()
            proc.setup("test",{
                "pipe": PIPE_LOCATION,
                "matcher" : "message REGEXP 'Testmessage from host (?P<HOST>\w+) received'",
                "format" : "#priority : #anotherfield - $HOST"
            })
            event1 = {
                "message" : 'Testmessage from host test123 received',
                "priority" : 1,
                'anotherfield' : 5
            }
            proc.process(event1)
            f.seek(0)
            line = f.readline()
            assert line.endswith("1 : 5 - test123\n")
        finally:
            self.remove_temporary_file()
            
        
    def test_formatted_command_submit_uc(self):
        try:
            f = open(PIPE_LOCATION,"w+")

            proc = CommandProcessor()
            proc.setup("test",{
                "pipe": PIPE_LOCATION,
                "matcher" : "message REGEXP 'Testmessage from host (?P<HOST>\w+) received'",
                "format" : "#priority : #anotherfield - $HOST",
                "uppercasetokens": True
            })
            event1 = {
                "message" : 'Testmessage from host test123 received',
                "priority" : 1,
                'anotherfield' : 5
            }
            proc.process(event1)
            f.seek(0)
            line = f.readline()
            assert line.endswith("1 : 5 - TEST123\n")
        finally:
            self.remove_temporary_file()