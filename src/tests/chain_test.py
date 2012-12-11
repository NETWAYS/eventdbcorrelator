import unittest
import logging
import time
from chain import Chain


class TestProcessorMock(object):
    def __init__(self):
        self.status = "OK"
        
    def setStatus(self, status):
        self.status = status
        
    def process(self, ev):
        return self.status

class ChainInMock(object):
    def __init__(self):
        self.queues = []
    
    def clear(self):
        self.queues = []    
        
    def register_queue(self, queue):
        self.queues.append(queue)
    
    def unregister_queue(self, queue):
        if queue in self.queues:
            self.queues.remove(queue)
    
    def fire_event(self, event):
        for queue in self.queues:
            queue.put(event)
    
class ChainOutMock(object):
    def __init__(self):
        self.events = []
    def clear(self):
        self.event = []
    def process(self, event):
        self.events.append(event)
    

class ChainTestCase(unittest.TestCase):
    
    def setUp(self):
        self.inMock = ChainInMock()
        self.outMock = ChainOutMock()
        self.testProcessorMock = TestProcessorMock()
        
        self.CHAIN_NO_CONDITION_SINGLE_OUT = {
            "in": self.inMock,
            "to_1": self.outMock
        }
        
        self.CHAIN_NO_CONDITION_MULTI_OUT = {
            "in": self.inMock,
            "to_1": self.outMock,
            "to_2": self.outMock
        }
        
        self.CHAIN_SINGLE_CONDITION_SINGLE_OUT = {
            "in": self.inMock,
            "to_1": self.testProcessorMock,
            "to_1[ok]_2": self.outMock
        }
        
        self.CHAIN_MSG_MATCHER_SINGLE_OUT = {
            "in": self.inMock,
            "matcher" : "message IS 'test'",
            "to_1": self.outMock
        }
        
    
    def _get_test_chain(self, testcase):
        self.inMock.clear()
        self.outMock.clear()

        test_chain = Chain()
        test_chain.setup("test", testcase)
        test_chain.setup_event_path()
        return test_chain


    def test_direct_write_no_condition(self):
        try:
            test_chain = self._get_test_chain(self.CHAIN_NO_CONDITION_SINGLE_OUT)
            test_chain.start()

            # The chain doesn't require a event to be from the Event class,
            # as it only concerns about event routing
            test_chain.input.fire_event("Test")
            time.sleep(0.01) # We're working with threads, so this might take a delay
            assert len(self.outMock.events) == 1
            assert self.outMock.events[0] == "Test"
        finally:
            test_chain.stop()
        

    def test_multi_write_no_condition(self):
        test_chain = self._get_test_chain(self.CHAIN_NO_CONDITION_MULTI_OUT)

        try:
            test_chain.start()

            test_chain.input.fire_event("Test")
            time.sleep(0.01) # We're working with threads, so this might take a delay
            assert len(self.outMock.events) == 2
            assert self.outMock.events[0] == self.outMock.events[1] == "Test"
        finally:
            test_chain.stop()

    
    def test_chain_with_matcher(self):
        try:
            test_chain = self._get_test_chain(self.CHAIN_MSG_MATCHER_SINGLE_OUT)
            test_chain.start()

            test_chain.input.fire_event({"message" : "test"})
            test_chain.input.fire_event({"message" : "testWorscht"})
            time.sleep(0.01) # We're working with threads, so this might take a delay
            assert len(self.outMock.events) == 1
            assert self.outMock.events[0] == {"message" : "test"}
            
            
        finally:
            test_chain.stop()


    def test_dependent_chains(self):
        try:
            test_chain = self._get_test_chain(self.CHAIN_MSG_MATCHER_SINGLE_OUT)

            out2 = ChainOutMock()
            out3 = ChainOutMock()
            dependentChain1 = Chain()
            dependentChain1.setup("test2", {
                "after": test_chain,
                "to_1": out2
            })
            dependentChain1.setup_event_path()
            
            dependentChain2 = Chain()
            dependentChain2.setup("test2", {
                "not_after": test_chain,
                "to_1": out3
            })
            dependentChain2.setup_event_path()
            
            
            test_chain.start()
            test_chain.input.fire_event({"message":"Test"})
            test_chain.input.fire_event({"message":"Not matching"})
            
            time.sleep(0.01) # We're working with threads, so this might take a delay
            assert len(self.outMock.events) == len(out2.events) == 1
            logging.debug(out3.events)
            assert len(out3.events) == 1
            assert self.outMock.events[0] == out2.events[0] == {"message":"Test"}
            assert out3.events[0] == {"message":"Not matching"}
            
        finally:
            test_chain.stop()


    def test_direct_write_single_condition(self):
        try:
            test_chain = self._get_test_chain(self.CHAIN_SINGLE_CONDITION_SINGLE_OUT)
            test_chain.start()
            self.testProcessorMock.setStatus("ok")
            
            test_chain.input.fire_event("test")
            time.sleep(0.01) # We're working with threads, so this might take a delay
            assert len(self.outMock.events) == 1
            assert self.outMock.events[0] == "test"
            
            self.testProcessorMock.setStatus("fail")
            test_chain.input.fire_event("test")
            time.sleep(0.01) # We're working with threads, so this might take a delay
            assert len(self.outMock.events) == 1
            '''
            self.testProcessorMock.setStatus("fail")
            test_chain.input.fire_event("test2")
            time.sleep(0.01) # We're working with threads, so this might take a delay
            assert len(self.outMock.events) == 2
            assert self.outMock.events[1] == "test2"
            '''          
        finally:
            test_chain.stop()
            
    def tearDown(self):
        pass
