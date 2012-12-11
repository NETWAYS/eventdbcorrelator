import unittest
from processors import ModifierProcessor
from event import Event
import time
import logging

class MockDataSource(object):
    def __init__(self):
        self.count = 0
        self.table = "test"
        self.groups = {}
        self.flushed = []
        
        
    def get_group_leader(self, group_id):
        if group_id in self.groups:
            return (self.groups[group_id], time.time())
        return (None, time.time())
    
    def execute_after_flush(self, query, args = ()):
        self.flushed.append(query)
        
    def reset(self):
        self.flushed = []
        
class ModifierProcessorTest(unittest.TestCase):
    
    def test_event_overwrite(self):
        event = {
            "ack" : 0,
            "test" : 1,
            "test2" : "string"
        }
        
        processor = ModifierProcessor()
        processor.setup("test",{
            "overwrite" : "test=4;test2=test",
            "target" : "event"
        })
        
        assert processor.process(event) == "OK"
        assert event["test"] == '4'
        assert event["test2"] == "test"
        assert event["ack"] == 0
        
        processor.setup("test",{
            "overwrite" : "test=4;test2=test",
            "target" : "event",
            "acknowledge" : "True"
        })
        assert processor.process(event) == "OK"
        assert event["ack"] == 1

        
    def test_group_overwrite(self):
        ds = MockDataSource()
        event = {
            "ack" : 0,
            "test" : 1,
            "test2" : "string",
            "group_id" : 'test',
            "group_leader" : '12345'
            
        }
        
        processor = ModifierProcessor()
        processor.setup("test",{
            "overwrite" : "test=4;test2=test",
            "target" : "group"
        })
        
        assert processor.process(event) == "PASS" # No datasource
        ds.reset()
        processor.setup("test",{
            "overwrite" : "test=4;test2=test",
            "target" : "group",
            "datasource" : ds
        })
        
        assert processor.process(event) == "OK"
        assert len(ds.flushed) == 1
        
