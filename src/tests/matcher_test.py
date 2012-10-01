# To change this template, choose Tools | Templates
# and open the template in the editor.

import unittest
import logging
import time

from event import *


class MatcherTestCase(unittest.TestCase):
    def test_simple_message(self):
        curMatcher = Matcher("(message is 'i am a testmessage')")

        testEvent = Event("I AM A Testmessage")
        assert curMatcher.matches(testEvent) == True

        testEvent = Event("I AM A non matching Testmessage")
        assert curMatcher.matches(testEvent) == False
        
        curMatcher = Matcher("(message is 'i am a testmessage') OR (source in ('snmp')) AND test = 123")        
        testEvent = Event("I AM A Testmessage")
        # Should be true as the left part is not evaluated
        assert curMatcher.matches(testEvent) == True
        
        testEvent = Event("I AM A non matching Testmessage")
        assert curMatcher.matches(testEvent) == False

        curMatcher = Matcher("(message starts with 'i am a testmessage') or message ends with 'test123'")
        
        testEvent = Event("I AM A non matching Testmessage")
        assert curMatcher.matches(testEvent) == False

        testEvent = Event("I AM A Testmessage")
        assert curMatcher.matches(testEvent) == True
        testEvent = Event("Idsfdsfdsfdsfdsf AM A Testmessage test123")

        assert curMatcher.matches(testEvent) == True
        
        curMatcher = Matcher("(message REGEXP 'Test\w+ [test]+123$' )")
        assert curMatcher.matches(testEvent) == True


    def test_simple_message_negate(self):
        curMatcher = Matcher("(message is not 'i am a testmessage')")
        testEvent = Event("I AM A Testmessage")
        assert curMatcher.matches(testEvent) == False

        testEvent = Event("I AM A non matching Testmessage")
        assert curMatcher.matches(testEvent) == True
        
        curMatcher = Matcher("(message is not 'i am a testmessage') OR (source in ('snmp')) AND test = 123")        
        testEvent = Event("I AM A Testmessage")
        # Should be true as the left part is not evaluated
        assert curMatcher.matches(testEvent) == False
        
        testEvent = Event("I AM A non matching Testmessage")
        assert curMatcher.matches(testEvent) == True

        
        
    def test_simple_numeric(self):
        testEvent = Event("ignore my message",time.ctime(),{
            "severity" : 4,
            "availability" : 0.995
        })
        
        curMatcher = Matcher("severity > 3")
        assert curMatcher.matches(testEvent) == True
        
        curMatcher = Matcher("severity = 3")
        assert curMatcher.matches(testEvent) == False
        
        curMatcher = Matcher("severity >= 4")
        assert curMatcher.matches(testEvent) == True
        
        curMatcher = Matcher("severity <= 4")
        assert curMatcher.matches(testEvent) == True
        
        curMatcher = Matcher("severity = 4")
        assert curMatcher.matches(testEvent) == True
        
        curMatcher = Matcher("severity != 4")
        assert curMatcher.matches(testEvent) == False
        
        curMatcher = Matcher("severity != 3")
        assert curMatcher.matches(testEvent) == True
        
        curMatcher = Matcher("availability > 0.99")
        assert curMatcher.matches(testEvent) == True
        
        curMatcher = Matcher("availability < 1")
        assert curMatcher.matches(testEvent) == True
        
    def test_simple_set(self):
        testEvent = Event("ignore my message",time.ctime(),{
            "severity" : 6,
            "source" : 'snmp'
        })
        curMatcher = None

        curMatcher = Matcher("severity IN (1,2,3,4,5)")
        assert curMatcher.matches(testEvent) == False

        curMatcher = Matcher("severity IN (1,2,3,4,5,6)")
        assert curMatcher.matches(testEvent) == True

        curMatcher = Matcher("severity NOT IN (1,2,3,4,5)")
        assert curMatcher.matches(testEvent) == True

        curMatcher = Matcher("severity NOT IN (1,2,3,4,5,6)")
        assert curMatcher.matches(testEvent) == False

        
        curMatcher = Matcher("source IN ('j2ee','snmp')")
        assert curMatcher.matches(testEvent) == True

        curMatcher = Matcher("source NOT IN ('snmp','j2ee')")
        assert curMatcher.matches(testEvent) == False

    def test_mixed(self):
        testEvent = Event("[LINK DOWN] eth0 on localhost is down.",time.ctime(),{
            "severity" : 7,
            "facility" : 4,
            "host" : "localhost",
            "program" : "NetworkManager"
        })
        
        #curMatcher = Matcher("message RE")