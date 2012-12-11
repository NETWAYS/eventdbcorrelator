import unittest
import threading

from datasource import MysqlDatasource, DBTransformer
from event.event import *
from event import ip_address
from processors import AggregationProcessor
from tests.mysql_datasource_test import SETUP_DB_FLUSHING

SETUP_DB = SETUP_DB_FLUSHING
MAX_TIME_PER_EVENT=0.001

class TestAggregationInsertionThread(threading.Thread):
    def setup(self, aggregator, count, evCfg, db):
        self.aggregator = aggregator
        self.events = []
        self.db = db
        for i in range(0, count):
            self.events.append(Event(message="test "+str(i), additional=evCfg))
    
    def run(self):
        self.burst_events()
        
        
    def burst_events(self):
        for i in self.events:
            self.aggregator.process(i)
            self.db.insert(i)
        
        
        

class AggregatorMysqlTest(unittest.TestCase):
    
    def setUp(self):
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
