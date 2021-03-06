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
import threading

from datasource import MysqlDatasource, DBTransformer
from event import  Event
from network import ip_address
from processors import AggregationProcessor
from tests.mysql_datasource_test import SETUP_DB_FLUSHING

SETUP_DB = SETUP_DB_FLUSHING
MAX_TIME_PER_EVENT=0.001

class TestAggregationInsertionThread(threading.Thread):
    """ Testthread that aggregates and inserts events and simulates an event burst
    """

    def setup(self, aggregator, count, evCfg, db):
        """ Sets up the thread with the aggregator, how much events should be inserted,
            how events look like and where to persist them
        """
        self.aggregator = aggregator
        self.events = []
        self.db = db
        for i in range(0, count):
            self.events.append(Event(message = "test "+str(i), additional = evCfg))
    
    def run(self):
        """ Thread entry point, runs burst_event
        """
        self.burst_events()
        
        
    def burst_events(self):
        """ runs through all events and processes/inserts them
        """
        for i in self.events:
            self.aggregator.process(i)
            self.db.insert(i)


class AggregatorMysqlTest(unittest.TestCase):
    """ Integration test of aggregators and mysqldatasources

    """

    def setUp(self):
        """ Creates and cleans up the datasource

        """
        self.source = MysqlDatasource()
        dbsetup = SETUP_DB
        dbsetup["transform"] = DBTransformer()
        self.source.setup("test", SETUP_DB)
        # Try tearing down the database in case a previous run ran wihtou cleanup
        try: 
            self.source.test_teardown_db()
            self.source.close(True)
        except:
            pass

        
    def test_new_aggregation_group(self):
        """ Tests the creation of a new aggregation group and
            if it's persisted correctly

        """
        try:
            self.source.test_setup_db()
            aggregator = AggregationProcessor()

            aggregator.setup("test",{
                "matcherfield": "message",
                "datasource"  : self.source
            })
            cfg = {
                "program"       : "testcase",
                "host_name"     : "localhost",
                "host_address"  : ip_address.IPAddress("127.0.0.1"),
                "source"        : 'snmp',
                "facility"      : 5,
                "priority"      : 0,
                "ack"           : 0
            }
            
            event1 = Event(message="test 1234", additional=cfg)
            event2 = Event(message="test 1234", additional=cfg)
            event3 = Event(message="test 1234", additional=cfg)
            event4 = Event(message="test 1234", additional=cfg)
            
            assert aggregator.process(event1) == "NEW" 
            self.source.insert(event1)
            
            assert aggregator.process(event2) == \
                aggregator.process(event3) == \
                aggregator.process(event4) == "AGGR"

            self.source.insert(event2)
            self.source.insert(event3)
            self.source.insert(event4)
            
            assert event1.group_leader == -1
            
            assert event2.group_leader == \
                   event3.group_leader == \
                   event4.group_leader == event1["id"]
            
        finally:
            self.source.test_teardown_db()
            self.source.close(True)
            
            
    
    def test_aggregation_group_timeout(self):
        """ Tests if groups are cleared automatically after the aggregation timeout
            has passed
        """
        try:
            self.source.test_setup_db()
            aggregator = AggregationProcessor()

            aggregator.setup("test",{
                "matcherfield": "message",
                "maxdelay"    : 1,
                "datasource"  : self.source
            })
            cfg = {
                "program"       : "testcase",
                "host_name"     : "localhost",
                "host_address"  : ip_address.IPAddress("127.0.0.1"),
                "source"        : 'snmp',
                "facility"      : 5,
                "priority"      : 0,
                "ack"           : 0
            }
            
            event1 = Event(message="test 1234", additional=cfg)
            event2 = Event(message="test 1234", additional=cfg)
            event3 = Event(message="test 1234", additional=cfg)
            event4 = Event(message="test 1234", additional=cfg)
            
            assert aggregator.process(event1) == "NEW" 
            self.source.insert(event1)
            assert event1["group_autoclear"] == 0
            assert aggregator.process(event2) == "AGGR"
            self.source.insert(event2)


            time.sleep(1.1) # wait for timeout
            
            assert aggregator.process(event3) == "NEW" 
            self.source.insert(event3)
            assert aggregator.process(event4) == "AGGR"
            self.source.insert(event4)
            
            assert event1.group_leader == event3.group_leader == -1
            assert event2.group_leader == event1["id"]
            assert event4.group_leader == event3["id"]

        finally:
            self.source.test_teardown_db()
            self.source.close(True)
            
    
    
    def test_aggregation_group_clear_message(self):
        """ Tests whether clear messages are correctly recognized and
            persisted on the database side

        """
        try:
            self.source.test_setup_db() 
            self.source.flush_interval = 1000 
            aggregator = AggregationProcessor()

            aggregator.setup("test",{
                "matcherfield": ".* 1234",
                "datasource"  : self.source,
                "clear"       : "message STARTS WITH 'clear'" 
            })
            cfg = {
                "program"       : "testcase",
                "host_name"     : "localhost",
                "host_address"  : ip_address.IPAddress("127.0.0.1"),
                "source"        : 'snmp',
                "facility"      : 5,
                "priority"      : 0,
                "ack"           : 0
            }
            
            event1 = Event(message="test 1234", additional=cfg)
            event2 = Event(message="test 1234", additional=cfg)
            event3 = Event(message="clear 1234", additional=cfg)
            event4 = Event(message="test 1234", additional=cfg)
            
            assert aggregator.autoclear == False
            assert aggregator.process(event1) == "NEW" 
            assert event1["group_autoclear"] == 0
            self.source.insert(event1)
            assert aggregator.process(event2) == "AGGR"
            self.source.insert(event2)
            self.source.insert(event2)
            self.source.insert(event2)
            self.source.insert(event2)
            self.source.insert(event2)
            self.source.insert(event2)
            self.source.insert(event2)
            self.source.insert(event2)
            self.source.insert(event2)
            
            assert aggregator.process(event3) == "CLEAR" 
            self.source.insert(event3)
    
            assert aggregator.process(event4) == "NEW"
            self.source.insert(event4)
            
            assert event1.group_leader == -1
            assert event2.group_leader == event1["id"]
            assert event3.group_leader == None
            assert event4.group_leader == -1
             
            time.sleep(1.5)    
            dbResult = self.source.execute("SELECT group_active, group_count FROM %s WHERE id = %s" % (self.source.table, event1["id"]))
            assert dbResult != None

            # Group should be active=0
            assert dbResult[0][0] == 0
            # Group should be 10 items big
            assert dbResult[0][1] == 10

        finally:
            self.source.test_teardown_db()
            self.source.close(True)
            
    def test_aggregation_with_autoack(self):
        """ Tests whether automatic acknowledgement is working correctly
            when a group is cleared

        """
        try:
            self.source.test_setup_db() 
            self.source.flush_interval = 1000 
            aggregator = AggregationProcessor()

            aggregator.setup("test",{
                "matcherfield": ".* 1234",
                "datasource"  : self.source,
                "clear"       : "message STARTS WITH 'clear'", 
                "acknowledge_on_clear" : True
            })
            cfg = {
                "program"       : "testcase",
                "host_name"     : "localhost",
                "host_address"  : ip_address.IPAddress("127.0.0.1"),
                "source"        : 'snmp',
                "facility"      : 5,
                "priority"      : 0,
                "ack"           : 0
            }
            
            event1 = Event(message="test 1234", additional=cfg)
            event2 = Event(message="test 1234", additional=cfg)
            event3 = Event(message="clear 1234", additional=cfg)
            event4 = Event(message="test 1234", additional=cfg)
            
            assert aggregator.autoclear == True
            assert aggregator.process(event1) == "NEW" 
            assert event1["group_autoclear"] == 1
            self.source.insert(event1)
            assert aggregator.process(event2) == "AGGR"
            self.source.insert(event2)
            self.source.insert(event2)
            self.source.insert(event2)
            self.source.insert(event2)
            self.source.insert(event2)
            self.source.insert(event2)
            self.source.insert(event2)
            self.source.insert(event2)
            self.source.insert(event2)
            
            assert aggregator.process(event3) == "CLEAR" 
            assert event3["ack"] == True
            self.source.insert(event3)
    
            assert aggregator.process(event4) == "NEW"
            self.source.insert(event4)
            
            assert event1.group_leader == -1
            assert event2.group_leader == event1["id"]
            assert event3.group_leader == None
            assert event4.group_leader == -1
             
            time.sleep(1.5)    
            dbResult = self.source.execute("SELECT COUNT(id) FROM %s WHERE (group_leader = %s OR id = %s) AND ack=1" % (self.source.table, event1["id"], event1["id"]))
            assert dbResult != None

            # Assert 10 items returned
            assert dbResult[0][0] == 10
            

        finally:
            self.source.test_teardown_db()
            self.source.close(True)
#            
#    def test_aggregation_group_performance(self):
#        try: 
#            self.source.test_setup_db()
#            aggregator = AggregationProcessor()
#
#            aggregator.setup("test",{
#                "matcherfield": "test .*",
#                "datasource"  : self.source,
#                "clear"       : "message STARTS WITH 'clear'" 
#            })
#            eventThreads = []
#            NR_OF_THREADS=10
#            NR_OF_EVENTS=200
#            for i in range(0, NR_OF_THREADS):
#                thread = TestAggregationInsertionThread()
#                thread.setup(aggregator, NR_OF_EVENTS,{
#                    "program"       : "testcase",
#                    "host_name"     : "localhost",
#                    "host_address"  : ip_address.IPAddress("127.0.0.1"),
#                    "source"        : 'snmp',
#                    "facility"      : 5,
#                    "priority"      : 0,
#                    "ack"           : 0
#                }, self.source)
#                eventThreads.append(thread)
#
#            start = time.time()
#
#            for i in eventThreads:
#                i.start()
#
#            for i in eventThreads:
#                i.join()
#
#            end = time.time()
#            assert (end-start)/(NR_OF_THREADS*NR_OF_EVENTS) <= MAX_TIME_PER_EVENT
#            
#        finally:
#            self.source.test_teardown_db()
#            self.source.close(True)
#	
