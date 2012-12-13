"""
EDBC - Message correlation and aggregation engine for passive monitoring events
Copyright (C) 2012  NETWAYS GmbH

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""
import unittest
import logging
import time
from chain import Chain

class TestProcessorMock(object):
    """ Mock for processors, always returns a predefined return code when
        processing

    """


    def __init__(self):
        self.status = "OK"
        
    def setStatus(self, status):
        """ Set the status process should return

        """
        self.status = status
        
    def process(self, event):
        """ Returns the predefined status value

        """
        return self.status


class ChainInMock(object):
    """ Mock for chain input sources, fulls the queue when fire_event is called

    """


    def __init__(self):
        self.queues = []
    
    def clear(self):
        """ Removes all registered queues
        """
        self.queues = []    
        
    def register_queue(self, queue):
        """ registers a new queue in this mock
        """
        self.queues.append(queue)
    
    def unregister_queue(self, queue):
        """ removes a queue from the registration
        """
        if queue in self.queues:
            self.queues.remove(queue)
    
    def fire_event(self, event):
        """ forwards event to all registered queues
        """
        for queue in self.queues:
            queue.put(event)


class ChainOutMock(object):
    """ Simple processor mock that holds events in an internal list
    """


    def __init__(self):
        self.events = []

    def clear(self):
        """ Clear the internal event buffer
        """
        self.event = []

    def process(self, event):
        """ Adds event to the internal buffer
        """
        self.events.append(event)
    

class ChainTestCase(unittest.TestCase):
    """ Several tests for chain setup, event routing and conditional
        event branch execution

    """


    def setUp(self):
        """ Sets up the test chains for the single tests

        """
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
        """ returns a new chain with the given testcase setup

        """
        self.inMock.clear()
        self.outMock.clear()

        test_chain = Chain()
        test_chain.setup("test", testcase)
        test_chain.setup_event_path()
        return test_chain


    def test_direct_write_no_condition(self):
        """ Direct in->out writing without any conditional processors

        """
        test_chain = self._get_test_chain(self.CHAIN_NO_CONDITION_SINGLE_OUT)

        try:
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
        """ Tests a chain with multiple elements

        """
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
        """ Tests a chain that only will be processed if the matcher fits

        """
        test_chain = self._get_test_chain(self.CHAIN_MSG_MATCHER_SINGLE_OUT)
        try:
            test_chain.start()
            test_chain.input.fire_event({"message" : "test"})
            test_chain.input.fire_event({"message" : "testWorscht"})
            time.sleep(0.01) # We're working with threads, so this might take a delay
            assert len(self.outMock.events) == 1
            assert self.outMock.events[0] == {"message" : "test"}
            
            
        finally:
            test_chain.stop()


    def test_dependent_chains(self):
        """ Tests chain dependency (chain1 only after chain2 or nor after chain2)

        """
        test_chain = self._get_test_chain(self.CHAIN_MSG_MATCHER_SINGLE_OUT)
        try:
            out2 = ChainOutMock()
            out3 = ChainOutMock()
            dependentChain1 = Chain()
            dependentChain1.setup("test2",{
                "after": test_chain,
                "to_1": out2
            })
            dependentChain1.setup_event_path()
            
            dependentChain2 = Chain()
            dependentChain2.setup("test2",{
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
        """ Tests a simple in->out chain with a conditional processor

        """
        test_chain = self._get_test_chain(self.CHAIN_SINGLE_CONDITION_SINGLE_OUT)
        try:
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

        finally:
            test_chain.stop()
            
    def tearDown(self):
        """ no teardown operation

        """
        pass
