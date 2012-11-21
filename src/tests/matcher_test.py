# To change this template, choose Tools | Templates
# and open the template in the editor.

import unittest
import logging
import time

from event import *
t

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

        curMatcher = Matcher("(message starts with 'i am a testmessage') OR message ends with 'test123'")
        
        testEvent = Event("I AM A non matching Testmessage")
        assert curMatcher.matches(testEvent) == False

        testEvent = Event("I AM A Testmessage")
        assert curMatcher.matches(testEvent) == True
        testEvent = Event("Idsfdsfdsfdsfdsf AM A Testmessage test123")

        assert curMatcher.matches(testEvent) == True
        
        curMatcher = Matcher("(message REGEXP 'Test\w+ [test]+123$' )")
        assert curMatcher.matches(testEvent) == True

    def test_matcher_memory(self):
        testEvent = Event("test123 AM A Testmessage test123")

        curMatcher = Matcher("(message REGEXP '(?P<Group1>.*) AM A Testmessage' )")
        assert curMatcher.matches(testEvent) == True
        assert curMatcher["Group1"] == "test123"
   
        
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

    def test_ip_operators(self):
        testEvent = Event("blobb",time.ctime(),{
            "address": '192.168.67.3',
            
        })
        
        curMatcher = Matcher("address IN NETWORK '192.168.0.0/16'")
        assert curMatcher.matches(testEvent) == True
        
        curMatcher = Matcher("address NOT IN NETWORK '192.168.1.0/24'")
        assert curMatcher.matches(testEvent) == True
        
        curMatcher = Matcher("address IN NETWORK '192.168.1.0/24'")
        assert curMatcher.matches(testEvent) == False
        
        curMatcher = Matcher("address IN IP RANGE '192.168.1.0-192.169.1.1'")
        assert curMatcher.matches(testEvent) == True

        
    def test_mixed(self):
        testEvent = Event("[LINK DOWN] eth0 on localhost is down.",time.ctime(),{
            "severity" : 7,
            "facility" : 4,
            "host" : "localhost",
            "program" : "NetworkManager"
        })
        
        curMatcher = Matcher("message REGEXP '(?P<INTERFACE>eth\d+) on (?P<HOST>\w+ is down)' OR (host IS 'localhost' AND facility > 5) ")
        assert curMatcher.matches(testEvent)
        
        curMatcher = Matcher("message REGEXP '(?P<INTERFACE>eth[1-9]) on (?P<HOST>\w+ is down)' OR (host IS 'localhost' AND facility > 5) ")
        assert curMatcher.matches(testEvent) == False
        
        curMatcher = Matcher("message REGEXP '(?P<INTERFACE>eth[1-9]) on (?P<HOST>\w+ is down)' OR (host IS 'localhost' AND facility < 5) ")
        assert curMatcher.matches(testEvent) == True        
  
    @unit_disabled 
    def test_performance(self):

        curMatcher = Matcher("message REGEXP '(?P<INTERFACE>eth\d+) on (?P<HOST>\w+ is down)' OR (host IS 'localhost' AND facility > 5) AND (address IN NETWORK '192.168.170.0/26' OR address IN IP RANGE '192.168.100.0-192.168.120.255')")
        EVENT_HARDLIMIT_PER_EVENT=0.003
        COUNT = 20000
        
        import random
        events = []
        for i in range(0,COUNT):
            events.append(Event("[LINK DOWN] et.",time.ctime(),{
                "severity" : random.randint(0,10),
                "address" : "192.168.%i.%i" % (random.randint(0,255),random.randint(0,255)),
                "facility" : random.randint(0,10),
                "host" : ["localhost","sv-mail","sv-app","ts-1","ts-2"][random.randint(0,4)],
                "program" : ["NetworkManager","watchdog","kernel","syslog"][random.randint(0,3)]
            }))
    
        now = time.time()
        for event in events:
            curMatcher.matches(event)
        duration = time.time() - now
        try:
            assert duration/COUNT <= EVENT_HARDLIMIT_PER_EVENT
        except AssertionError, e:
            logging.debug("Performance test failed, request took %f seconds, limit was %f " % (duration/COUNT,EVENT_HARDLIMIT_PER_EVENT))
            raise e
