import unittest
from datasource import MysqlDatasource
import logging
import time
import MySQLdb

from event.event import Event
from event import ip_address


class DBTransformerMock(object):
    
    def transform(self,event):
        return {
            "host_name" : "test",
            "host_address" : event["host_address"].bytes,
            "type" : 1,
            "facility" : 1,
            "priority" : 1,
            "program" : event["program"],
            "message" : event["message"],
            "ack"     : 0,
            "created" : None,
            "modified": None
        }
    

#
# Your database requires read, write, create amd drop permissions for the user given here.
# 
SETUP_DB = {
    "host" : "127.0.0.1",
    "port" : 3306,
    "user" : "testcases",
    "password" : "testcases",
    "database" : "test_eventdb",
    "transform" : DBTransformerMock(),
    "noFlush" : True
}

SETUP_DB_FLUSHING = {
    "host" : "127.0.0.1",
    "port" : 3306,
    "user" : "testcases",
    "password" : "testcases",
    "database" : "test_eventdb",
    "transform" : DBTransformerMock(),
    "flush_interval": 1000
}

class MysqlDatasourceTest(unittest.TestCase):


    def setUp(self):
        self.source = MysqlDatasource()
        self.source.setup("test",SETUP_DB)
        # Try tearing down the database in case a previous run ran wihtou cleanup
        try: 
            self.source.test_teardown_db()
        except:
            pass
        
    
    def test_execute(self):
        logging.debug("exec")

        self.source.test_setup_db()
        try:
            result1 = self.source.execute("SELECT 'test',1,1.2,0xff from dual")
            for row in result1:
                assert row[0] == 'test'
                assert row[1] == 1
                assert float(row[2]) == float(1.2)
                assert ord(row[3]) == 0xff
            
            #test with argument list
            result2 = self.source.execute("SELECT %s,%s,%s,%s from dual",('test',1,1.2,0xff ))
            for row in result2:
                assert row[0] == 'test'
                assert row[1] == 1
                assert float(row[2]) == float(1.2)
                assert row[3] == 0xff

        finally:
            self.source.test_teardown_db()


    '''
    Tests Create, Read, Update and Delete operations on this datasource.
    Not really an atomic test, but should do the job
    '''
    def test_crud(self):
        logging.debug("crud")

        self.source.test_setup_db()
        ev = Event(message="testmessage",additional={
            "host_address": ip_address.IPAddress("192.168.178.56"),
            "program" : "test_program"
        })
        try:
            # Create
            assert self.source.insert(ev) == "OK"
            assert ev["id"]
            
            # Read
            ev_from_db = self.source.get_event_by_id(ev["id"])
            assert ev_from_db.message == "testmessage"
            assert ev_from_db["host_address"] == ip_address.IPAddress("192.168.178.56")
            assert ev_from_db["id"] == ev["id"]
            
            # Update
            ev["host_address"] = ip_address.IPAddress("192.168.178.57")
            ev["message"] = "testmessage2"
            self.source.update(ev)
            ev_from_db = self.source.get_event_by_id(ev["id"])
            assert ev_from_db.message == "testmessage2"
            assert ev_from_db["host_address"] == ip_address.IPAddress("192.168.178.57")
            assert ev_from_db["id"] == ev["id"]
            
            # Delete
            self.source.remove(ev)
            ev_from_db = self.source.get_event_by_id(ev["id"])
            assert ev_from_db == None
            
        finally:
            self.source.test_teardown_db()
  
  
    def test_message_overflow(self):
        logging.debug("overflow")
        try :
            self.source.test_setup_db()
            
            message = "test123456789"
            for i in range(0,10):
                message = message + message;

            ev = Event(message=message,additional={
                "host_address": ip_address.IPAddress("192.168.178.56"),
                "program" : "test_program"
            })
            self.source.insert(ev)
            
            ev_from_db = self.source.get_event_by_id(ev["id"])
            assert ev_from_db.message == message[0:4096] # assume data being truncated
        finally:
            self.source.test_teardown_db() 
        
    def test_group_implicit_insertion(self):
        logging.debug("implicit_insert")
        try:
            self.source.test_setup_db()
            ev = Event(message="test",additional={
                "host_address": ip_address.IPAddress("192.168.178.56"),
                "program" : "test_program",

                "priority" : 0,
                "facility" : 0,
                "active" : 1,
                "group_active" : True
            })
            ev.group_leader = -1
            ev.group_id = "test"
            self.source.insert(ev)
            leader = self.source.get_group_leader("test")
            assert leader != (None,None)
            assert leader[0] == ev["id"]
            lastmod = leader[1]
            time.sleep(1)
            
            # test moddate
            ev2 = Event(message="test",additional={
                "host_address": ip_address.IPAddress("192.168.178.56"),
                "program" : "test_program",
                "priority" : 0,
                "facility" : 0,
                "active" : 1,
                "group_active" : True
            })
            ev2.group_leader = ev["id"]
            ev2.group_id = "test"
            self.source.insert(ev2)
            
            leader = self.source.get_group_leader("test")
            assert leader != (None,None)
            assert leader[0] == ev["id"]
            assert lastmod != leader[1]
            assert self.source.connections.qsize() == self.source.poolsize
            
        finally:
            self.source.test_teardown_db()
    
    
    def test_id_generation(self):
        logging.debug("id_gen")
        try:
            self.source.test_setup_db()
            ev = Event(message="test",additional={
                "host_address": ip_address.IPAddress("192.168.178.56"),
                "program" : "test_program",

                "priority" : 0,
                "facility" : 0,
                "active" : 1,
                "group_active" : True
            })
            assert self.source.last_id == 0
            self.source.insert(ev)
            self.source.insert(ev)
            self.source.insert(ev)
            self.source.insert(ev)
            self.source.insert(ev)

            assert self.source.last_id == 5
            
            self.source.close()
            self.source = MysqlDatasource()
            self.source.setup("test",SETUP_DB)
            
            assert self.source.last_id == 5
            self.source.insert(ev)
            assert self.source.last_id == 6            
            assert self.source.connections.qsize() == self.source.poolsize
        finally:
            self.source.test_teardown_db()
    
    def test_id_generation_error(self):
        try:
            self.source.test_setup_db()
            ev = Event(message="test",additional={
                "host_address": ip_address.IPAddress("192.168.178.56"),
                "program" : "test_program",

                "priority" : 0,
                "facility" : 0,
                "active" : 1,
                "group_active" : True
            })
            assert self.source.last_id == 0
            self.source.insert(ev)
            self.source.insert(ev)
            self.source.insert(ev)
            self.source.last_id = 0
            self.source.insert(ev)
            self.source.insert(ev)
            
            assert self.source.last_id == 5
            
        finally:
            self.source.test_teardown_db()
    def test_group_persistence(self):
        logging.debug("group_persistence")
        try:
            self.source.test_setup_db()
            ev = Event(message="test",additional={
                "host_address": ip_address.IPAddress("192.168.178.56"),
                "program" : "test_program",

                "priority" : 0,
                "facility" : 0,
                "active" : 1,
                "group_active" : True
            })
            ev.group_leader = -1
            ev.group_id = "test\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            self.source.insert(ev)
            
            leader = self.source.get_group_leader("test\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
            assert leader != (None,None)
            assert leader[0] == ev["id"]
            
            self.source.close()
            
            self.source = MysqlDatasource()
            self.source.setup("test",SETUP_DB)
            self.source.connect()
                        
            leader = self.source.get_group_leader("test\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
            assert leader != (None,None)
            assert leader[0] == ev["id"]            
            assert self.source.connections.qsize() == self.source.poolsize
            
        finally:
            self.source.test_teardown_db()
        


    def test_async_flush(self):
        logging.debug("async_flush")
        try:
            self.source.test_setup_db()
            self.source.no_async_flush = False
            self.source.flush_interval = 500.0
            ev = Event(message="test",additional={
                "host_address": ip_address.IPAddress("192.168.178.56"),
                "program" : "test_program",

                "priority" : 0,
                "facility" : 0,
                "active" : 1,
                "group_active" : True
            })
            ev.group_leader = -1
            ev.group_id = "test\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            self.source.insert(ev)
            assert self.source.flush_pending == True 
            
            self.source.flush()
            assert self.source.flush_pending == True
            time.sleep(1)
            assert self.source.flush_pending == False
            assert self.source.connections.qsize() == self.source.poolsize
        finally:
            self.source.test_teardown_db()


    def tearDown(self):
        try: 
            self.source.test_teardown_db()
        except:
            pass
        pass
