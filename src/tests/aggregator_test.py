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
from processors import AggregationProcessor
from event import Event
import time

class MockDataSource(object):
    """ Mock datasource that returns groupleaders from an internal dictionary

    """


    def __init__(self):
        self.count = 0
        self.groups = {}

    def get_group_leader(self, group_id):
        """ returns the group_id entry from the public accessible 'groups' dict

        """
        if group_id in self.groups:
            return (self.groups[group_id], time.time())
        return (None, time.time())

    def deactivate_group(self,group_id):
        pass

    def acknowledge_group(self,arg1,arg2):
        pass

class AggregatorTestCase(unittest.TestCase):
    """ Tests for the AggregationProcessor

    """


    def test_hashing_with_matcher_fields(self):
        """ Tests hash generation when only using a single matcher field

        """

        processor = AggregationProcessor()
        processor2 = AggregationProcessor()

        processor.setup("test",{
            "matcherfield": 'message',
            "datasource"  : MockDataSource()
        })
        processor2.setup("test2",{
            "matcherfield": 'message',
            "datasource"  : MockDataSource()
        })
        event1 = {
            "message" : 'Arbitary message as this shouldn\'t matter',
            'anotherfield' : 'test'
        }
        event2 = {
            "message" : 'Arbitary message as this shouldn\'t matter2',
            'anotherfield2' : 'test'
        }
        event3 = {
            "message" : 'Arbitary message as this shouldn\'t matter',
            'anotherfield3' : 'test123'
        }

        assert processor.process(event1) == "NEW"
        assert processor.process(event2) == "NEW"
        assert processor2.process(event3) == "NEW"
        
        assert "group_id" in event1
        assert "group_id" in event2
        assert "group_id" in event3
        
        assert event1["group_id"] != event2["group_id"]
        assert event1["group_id"] != event3["group_id"]
        
        processor.process(event3)
        assert event1["group_id"] == event3["group_id"]
    
    
    def test_hashing_with_multiple_matcher_fields(self):
        """ Tests hash (group_id) generation when using multiple matcher fields

        """

        processor = AggregationProcessor()
        processor.setup("test",{
            "matcherfield": 'message, priority',
            "datasource"  : MockDataSource()
        })
        
        event1 = {
            "message" : 'Testmessage',
            "priority" : 1,
            'anotherfield' : 5
        }
        event2 = {
            "message" : 'Testmessage',
            "priority" : 2,
            'anotherfield' : 4
        }
        event3 = {
            "message" : 'Testmessage',
            "priority" : 2,
            'anotherfield' : 6
        }
        
        processor.process(event1)
        processor.process(event2)
        processor.process(event3)
        
        assert "group_id" in event1
        assert "group_id" in event2
        assert "group_id" in event3
        
        assert event1["group_id"] != event2["group_id"]
        assert event1["group_id"] != event3["group_id"]
        assert event2["group_id"] == event3["group_id"]

    def test_hashing_with_message_analysis(self):
        """  Tests recognition of matching groups and hash generation based upon them

        """

        processor = AggregationProcessor()
        processor.setup("test",{
            "matcher": "message REGEXP '^(?P<HOST>\w+) is (?P<STATUS>(UP|DOWN))'",
            "datasource"  : MockDataSource()
        })
        
        event1 = {"message" : 'localhost is up'}
        event2 = {"message" : 'localhost is down'}
        event3 = {"message" : 'localhost is up'}
        event4 = {"message" : 'WARNING: localhost is down'}
        
        processor.process(event1)
        processor.process(event2)
        processor.process(event3)
        assert processor.process(event4) == "PASS"
        
        assert "group_id" in event1
        assert "group_id" in event2
        assert "group_id" in event3
        
        assert event1["group_id"] != event2["group_id"]
        assert event1["group_id"] == event3["group_id"]

    def test_hashing_with_message_analysis_and_fields(self):
        """ Tests combinations of matcherfields and regexp groups for hash generation

        """
        processor = AggregationProcessor()
        processor.setup("test",{
            "matcher": "message REGEXP '^(?P<HOST>\w+) is (?P<STATUS>(UP|DOWN))'",
            "matcherfield": 'priority',
            "datasource"  : MockDataSource()
        })
        
        event1 = {"message" : 'localhost is up', "priority" : 3}
        event2 = {"message" : 'localhost is up', "priority" : 1}
        event3 = {"message" : 'localhost is up', "priority" : 3}
        event4 = {"message" : 'WARNING: localhost is up', "priority" : 4}
        event5 = Event(message='localhost is up')
        
        processor.process(event1)
        processor.process(event2)
        processor.process(event3)
        assert processor.process(event4) == "PASS"
        processor.process(event5)
        
        assert "group_id" in event1
        assert "group_id" in event2
        assert "group_id" in event3
        assert event5["group_id"] 

        assert event1["group_id"] != event2["group_id"]
        assert event1["group_id"] == event3["group_id"]
        assert event1["group_id"] != event5["group_id"]
        assert event2["group_id"] != event5["group_id"]
        
    def test_add_to_group(self):
        """ Tests if events are correctly added to an existing group if the
            hash (group id) is the same

        """
        processor = AggregationProcessor()
        ds = MockDataSource()
        
        processor.setup("test",{
            "matcher": "message REGEXP '^(?P<HOST>\w+) is (?P<STATUS>(UP|DOWN))'",
            "datasource"  : ds
        })
        
        event1 = {"message" : 'localhost is up', "priority" : 3}
        event2 = {"message" : 'localhost is up', "priority" : 1}
        
        assert processor.process(event1) == "NEW"
        assert "group_id" in event1
        ds.groups[event1["group_id"]] = event1
        
        assert processor.process(event2) == "AGGR"
        assert "group_id" in event2
        
        assert event2["group_id"] == event1["group_id"]
        

    def test_use_case_AIC(self):

        processor = AggregationProcessor()
        ds = MockDataSource()

        processor.setup("test", {
            "matcher" : "snmp_var_.1.3.6.1.6.3.1.1.4.1.0 is '.1.3.6.1.4.1.192.6.4.19.0.1' OR snmp_var_.1.3.6.1.6.3.1.1.4.1.0 is '.1.3.6.1.4.1.192.6.4.19.0.2'",
            "matcherfield" : "snmp_var_.1.3.6.1.4.1.192.6.4.19.1.2",
            "clear" : "snmp_var_.1.3.6.1.6.3.1.1.4.1.0 is '.1.3.6.1.4.1.192.6.4.19.0.2'",
            "datasource" : ds
        })
        event1 = {'message' : '','snmp_var_.1.3.6.1.4.1.192.6.4.19.1.6': 'Login to AIC system and restart process.', 'ack': 0, 'facility': '5', 'snmp_var_.1.3.6.1.4.1.192.6.4.19.1.5': '../log/snmp_test_20130308<br><A href="https://wiki.materna-com.de/index.php/Trap_MT-MT-BC-GSMC-MIB::mtMtBcGSMCProcessError>further&#32;details</A>', 'priority': 2, 'snmp_var_.1.3.6.1.2.1.1.3.0': '0:0:00:00.10', 'snmp_var_.1.3.6.1.4.1.192.6.4.19.1.4': "Can't connect to 127.0.0.1:12345", 'program': 'snmp', 'snmp_var_.1.3.6.1.4.1.192.6.4.19.1.2': 'TEST0', 'host_name': 'test-xymon-client.materna-com.de', 'snmp_var_.1.3.6.1.4.1.192.6.4.19.1.1': 'An error occured at AIC system, process <TEST0>', 'snmp_var_.1.3.6.1.6.3.1.1.4.1.0': '.1.3.6.1.4.1.192.6.4.19.0.1'}
        event2 = {'message' : '','snmp_var_.1.3.6.1.4.1.192.6.4.19.1.6': 'Login to AIC system and restart process.', 'ack': 0, 'facility': '5', 'snmp_var_.1.3.6.1.4.1.192.6.4.19.1.5': '../log/snmp_test_20130308<br><A href="https://wiki.materna-com.de/index.php/Trap_MT-MT-BC-GSMC-MIB::mtMtBcGSMCProcessError>further&#32;details</A>', 'priority': 2, 'snmp_var_.1.3.6.1.2.1.1.3.0': '0:0:00:00.10', 'snmp_var_.1.3.6.1.4.1.192.6.4.19.1.4': "Can't connect to 127.0.0.1:12345", 'program': 'snmp', 'snmp_var_.1.3.6.1.4.1.192.6.4.19.1.2': 'TEST0', 'host_name': 'test-xymon-client.materna-com.de', 'snmp_var_.1.3.6.1.4.1.192.6.4.19.1.1': 'An error occured at AIC system, process <TEST0>', 'snmp_var_.1.3.6.1.6.3.1.1.4.1.0': '.1.3.6.1.4.1.192.6.4.19.0.1'}
        event3 = {'message' : '','snmp_var_.1.3.6.1.4.1.192.6.4.19.1.6': 'Login to AIC system and restart process.', 'ack': 0, 'facility': '5', 'snmp_var_.1.3.6.1.4.1.192.6.4.19.1.5': '../log/snmp_test_20130308<br><A href="https://wiki.materna-com.de/index.php/Trap_MT-MT-BC-GSMC-MIB::mtMtBcGSMCProcessError>further&#32;details</A>', 'priority': 2, 'snmp_var_.1.3.6.1.2.1.1.3.0': '0:0:00:00.10', 'snmp_var_.1.3.6.1.4.1.192.6.4.19.1.4': "Can't connect to 127.0.0.1:12345", 'program': 'snmp', 'snmp_var_.1.3.6.1.4.1.192.6.4.19.1.2': 'TEST0', 'host_name': 'test-xymon-client.materna-com.de', 'snmp_var_.1.3.6.1.4.1.192.6.4.19.1.1': 'An error occured at AIC system, process <TEST0>', 'snmp_var_.1.3.6.1.6.3.1.1.4.1.0': '.1.3.6.1.4.1.192.6.4.19.0.1'}
        event4 = {'message' : '','snmp_var_.1.3.6.1.4.1.192.6.4.19.1.6': 'Login to AIC system and restart process.', 'ack': 0, 'facility': '5', 'snmp_var_.1.3.6.1.4.1.192.6.4.19.1.5': '../log/snmp_test_20130308<br><A href="https://wiki.materna-com.de/index.php/Trap_MT-MT-BC-GSMC-MIB::mtMtBcGSMCProcessError>further&#32;details</A>', 'priority': 2, 'snmp_var_.1.3.6.1.2.1.1.3.0': '0:0:00:00.10', 'snmp_var_.1.3.6.1.4.1.192.6.4.19.1.4': "Can't connect to 127.0.0.1:12345", 'program': 'snmp', 'snmp_var_.1.3.6.1.4.1.192.6.4.19.1.2': 'TEST0', 'host_name': 'test-xymon-client.materna-com.de', 'snmp_var_.1.3.6.1.4.1.192.6.4.19.1.1': 'An error occured at AIC system, process <TEST0>', 'snmp_var_.1.3.6.1.6.3.1.1.4.1.0': '.1.3.6.1.4.1.192.6.4.19.0.2'}
        assert processor.process(event1) == "NEW"
        ds.groups[event1["group_id"]] = event1

        assert processor.process(event2) == "AGGR"
        assert processor.process(event3) == "AGGR"
        assert processor.process(event4) == "CLEAR"