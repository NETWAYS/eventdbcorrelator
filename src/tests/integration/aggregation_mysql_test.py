import unittest
from datasource import MysqlDatasource, DBTransformer, GROUP_NOT_EMPTY_FLAG
from event.event import *
from event import ip_address
from processors import AggregationProcessor
from tests.mysql_datasource_test import SETUP_DB, DBTransformerMock

class AggregatorMysqlTest(unittest.TestCase):
    
    def setUp(self):
        self.source = MysqlDatasource()
        dbsetup = SETUP_DB
        dbsetup["transform"] = DBTransformer()
        self.source.setup("test",SETUP_DB)
        # Try tearing down the database in case a previous run ran wihtou cleanup
        try: 
            self.source.test_teardown_db()
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