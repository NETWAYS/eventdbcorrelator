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
import time
from event import Event,Matcher

class MatcherTestCase(unittest.TestCase):
    """ Test cases for the matcher syntax

    """
    

    def test_simple_message(self):
        """ Tests for simple message checks and regexp

        """
    
        current_matcher = Matcher("(message is 'i am a testmessage')")

        testEvent = Event("I AM A Testmessage")
        assert current_matcher.matches(testEvent) == True

        testEvent = Event("I AM A non matching Testmessage")
        assert current_matcher.matches(testEvent) == False
        
        current_matcher = Matcher("(message is 'i am a testmessage') OR (source in ('snmp')) AND test = 123")
        testEvent = Event("I AM A Testmessage")
        # Should be true as the left part is not evaluated
        assert current_matcher.matches(testEvent) == True
        
        testEvent = Event("I AM A non matching Testmessage")
        assert current_matcher.matches(testEvent) == False

        current_matcher = Matcher("(message starts with 'i am a testmessage') OR message ends with 'test123'")
        
        testEvent = Event("I AM A non matching Testmessage")
        assert current_matcher.matches(testEvent) == False

        testEvent = Event("I AM A Testmessage")
        assert current_matcher.matches(testEvent) == True
        testEvent = Event("Idsfdsfdsfdsfdsf AM A Testmessage test123")

        assert current_matcher.matches(testEvent) == True
        
        current_matcher = Matcher("(message REGEXP 'Test\w+ [test]+123$' )")
        assert current_matcher.matches(testEvent) == True

    def test_matcher_memory(self):
        """ Tests if regular expression groups are stored in memory after a match
            
        """
        testEvent = Event("test123 AM A Testmessage test123")

        current_matcher = Matcher("(message REGEXP '(?P<Group1>.*) AM A Testmessage' )")
        assert current_matcher.matches(testEvent) == True
        assert current_matcher["Group1"] == "test123"
   
    def test_simple_message_negate(self):
        """ Same like simple message tests, but negated

        """
        current_matcher = Matcher("(message is not 'i am a testmessage')")
        testEvent = Event("I AM A Testmessage")
        assert current_matcher.matches(testEvent) == False

        testEvent = Event("I AM A non matching Testmessage")
        assert current_matcher.matches(testEvent) == True
        
        current_matcher = Matcher("(message is not 'i am a testmessage') OR (source in ('snmp')) AND test = 123")        
        testEvent = Event("I AM A Testmessage")
        # Should be true as the left part is not evaluated
        assert current_matcher.matches(testEvent) == False
        
        testEvent = Event("I AM A non matching Testmessage")
        assert current_matcher.matches(testEvent) == True

    def test_simple_numeric(self):
        """ Simple tests for numeric values (float and int)

        """
        testEvent = Event("ignore my message", time.ctime(),{
            "severity" : 4,
            "availability" : 0.995
        })
        
        current_matcher = Matcher("severity > 3")
        assert current_matcher.matches(testEvent) == True
        
        current_matcher = Matcher("severity = 3")
        assert current_matcher.matches(testEvent) == False
        
        current_matcher = Matcher("severity >= 4")
        assert current_matcher.matches(testEvent) == True
        
        current_matcher = Matcher("severity <= 4")
        assert current_matcher.matches(testEvent) == True
        
        current_matcher = Matcher("severity = 4")
        assert current_matcher.matches(testEvent) == True
        
        current_matcher = Matcher("severity != 4")
        assert current_matcher.matches(testEvent) == False
        
        current_matcher = Matcher("severity != 3")
        assert current_matcher.matches(testEvent) == True
        
        current_matcher = Matcher("availability > 0.99")
        assert current_matcher.matches(testEvent) == True
        
        current_matcher = Matcher("availability < 1")
        assert current_matcher.matches(testEvent) == True
        
    def test_simple_set(self):
        """ Simple tests for set operations 

        """
        testEvent = Event("ignore my message", time.ctime(),{
            "severity" : 6,
            "source" : 'snmp'
        })
        current_matcher = None

        current_matcher = Matcher("severity IN (1, 2, 3, 4, 5)")
        assert current_matcher.matches(testEvent) == False

        current_matcher = Matcher("severity IN (1, 2, 3, 4, 5, 6)")
        assert current_matcher.matches(testEvent) == True

        current_matcher = Matcher("severity NOT IN (1, 2, 3, 4, 5)")
        assert current_matcher.matches(testEvent) == True

        current_matcher = Matcher("severity NOT IN (1, 2, 3, 4, 5, 6)")
        assert current_matcher.matches(testEvent) == False

        
        current_matcher = Matcher("source IN ('j2ee','snmp')")
        assert current_matcher.matches(testEvent) == True

        current_matcher = Matcher("source NOT IN ('snmp','j2ee')")
        assert current_matcher.matches(testEvent) == False

    def test_ip_operators(self):
        """ IP operator tests
            
        """
        testEvent = Event("blobb", time.ctime(),{
            "address": '192.168.67.3',
            
        })
        
        current_matcher = Matcher("address IN NETWORK '192.168.0.0/16'")
        assert current_matcher.matches(testEvent) == True
        
        current_matcher = Matcher("address NOT IN NETWORK '192.168.1.0/24'")
        assert current_matcher.matches(testEvent) == True
        
        current_matcher = Matcher("address IN NETWORK '192.168.1.0/24'")
        assert current_matcher.matches(testEvent) == False
        
        current_matcher = Matcher("address IN IP RANGE '192.168.1.0-192.169.1.1'")
        assert current_matcher.matches(testEvent) == True

    def test_mixed(self):
        """ Tests of several conjunctions and different operators

        """
        testEvent = Event("[LINK DOWN] eth0 on localhost is down.", time.ctime(),{
            "severity" : 7,
            "facility" : 4,
            "host" : "localhost",
            "program" : "NetworkManager"
        })
        
        current_matcher = Matcher("message REGEXP '(?P<INTERFACE>eth\d+) on (?P<HOST>\w+ is down)' OR (host IS 'localhost' AND facility > 5) ")
        assert current_matcher.matches(testEvent)
        
        current_matcher = Matcher("message REGEXP '(?P<INTERFACE>eth[1-9]) on (?P<HOST>\w+ is down)' OR (host IS 'localhost' AND facility > 5) ")
        assert current_matcher.matches(testEvent) == False
        
        current_matcher = Matcher("message REGEXP '(?P<INTERFACE>eth[1-9]) on (?P<HOST>\w+ is down)' OR (host IS 'localhost' AND facility < 5) ")
        assert current_matcher.matches(testEvent) == True        
#  
#    def test_performance(self):
#
#        current_matcher = Matcher("message REGEXP '(?P<INTERFACE>eth\d+) on (?P<HOST>\w+ is down)' OR (host IS 'localhost' AND facility > 5) AND (address IN NETWORK '192.168.170.0/26' OR address IN IP RANGE '192.168.100.0-192.168.120.255')")
#        EVENT_HARDLIMIT_PER_EVENT=0.003
#        COUNT = 20000
#        
#        import random
#        events = []
#        for i in range(0, COUNT):
#            events.append(Event("[LINK DOWN] et.", time.ctime(),{
#                "severity" : random.randint(0, 10),
#                "address" : "192.168.%i.%i" % (random.randint(0, 255), random.randint(0, 255)),
#                "facility" : random.randint(0, 10),
#                "host" : ["localhost","sv-mail","sv-app","ts-1","ts-2"][random.randint(0, 4)],
#                "program" : ["NetworkManager","watchdog","kernel","syslog"][random.randint(0, 3)]
#            }))
#    
#        now = time.time()
#        for event in events:
#            current_matcher.matches(event)
#        duration = time.time() - now
#        try:
#            assert duration/COUNT <= EVENT_HARDLIMIT_PER_EVENT
#        except AssertionError, e:
#            logging.debug("Performance test failed, request took %f seconds, limit was %f " % (duration/COUNT, EVENT_HARDLIMIT_PER_EVENT))
#            raise e
