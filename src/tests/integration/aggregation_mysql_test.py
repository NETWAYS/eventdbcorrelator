import unittest
import threading

from datasource import MysqlDatasource, DBTransformer
from event.event import *
from event import ip_address
from processors import AggregationProcessor
from tests.mysql_datasource_test import SETUP_DB
MAX_TIME_PER_EVENT=0.001

class TestAggregationInsertionThread(threading.Thread):
    def setup(self,aggregator,count,evCfg,db):
        self.aggregator = aggregator
        self.events = []
        self.db = db
        for i in range(0,count):
            self.events.append(Event(message="test "+str(i),additional=evCfg))
    
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
        self.source.setup("test",SETUP_DB)
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
                "maxDelay"    : 1,
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
            
            assert aggregator.process(event1) == "NEW" 
            self.source.insert(event1)
            assert aggregator.process(event2) == "AGGR"
            self.source.insert(event2)
            
            assert aggregator.process(event3) == "CLEAR" 
            self.source.insert(event3)
            assert aggregator.process(event4) == "NEW"
            self.source.insert(event4)
            
            assert event1.group_leader == -1
            assert event2.group_leader == event1["id"]
            assert event3.group_leader == None
            assert event4.group_leader == -1
            
        finally:
            self.source.test_teardown_db()
            self.source.close(True)
            

    def test_aggregation_group_performance(self):
        try: 
            self.source.test_setup_db()
            aggregator = AggregationProcessor()

            aggregator.setup("test",{
                "matcherfield": "test .*",
                "datasource"  : self.source,
                "clear"       : "message STARTS WITH 'clear'" 
            })
            eventThreads = []
            NR_OF_THREADS=10
            NR_OF_EVENTS=10
            for i in range(0,NR_OF_THREADS):
                thread = TestAggregationInsertionThread()
                thread.setup(aggregator,NR_OF_EVENTS,{
                    "program"       : "testcase",
                    "host_name"     : "localhost",
                    "host_address"  : ip_address.IPAddress("127.0.0.1"),
                    "source"        : 'snmp',
                    "facility"      : 5,
                    "priority"      : 0,
                    "ack"           : 0
                },self.source)
                eventThreads.append(thread)

            start = time.time()

            for i in eventThreads:
                i.start()

            for i in eventThreads:
                i.join()

            end = time.time()
            assert (end-start)/(NR_OF_THREADS*NR_OF_EVENTS) <= MAX_TIME_PER_EVENT
            
        finally:
            self.source.test_teardown_db()
            self.source.close(True)
