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
from datasource import MysqlDatasource
import time
import MySQLdb

from event.event import Event
from network import ip_address

class DBTransformerMock(object):
    """ Transformer mock to resolve datasource dependencies
    """

    def transform(self, event):
        """ Transforms the event, using only the address, program and message
        """

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
    

class FailCursor(MySQLdb.cursors.Cursor):
    """ Cursor mock that inserts after the third try

    """
    tries = 0

    def __init__(self, conn):
        super(FailCursor,self).__init__(conn)
        self.executed = []


    def execute(self, query, args):
        if FailCursor.tries > 0:
            err = MySQLdb.OperationalError()
            FailCursor.tries -= 1
            raise err

        return super(FailCursor,self).execute(query,args)

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
    """ Several tests for the mysql datasource

    """

    def setUp(self):
        """ Creates the datasource and clears previous states
        """

        self.source = MysqlDatasource()
        self.source.setup("test", SETUP_DB)
        # Try tearing down the database in case a previous run ran wihtou cleanup
        try: 
            self.source.test_teardown_db()
        except:
            pass
        
    
    def test_execute(self):
        """ Tests the execute method by simply selecting dual values

        """
        self.source.test_setup_db()
        try:
            result1 = self.source.execute("SELECT 'test', 1, 1.2, 0xff from dual")
            for row in result1:
                assert row[0] == 'test'
                assert row[1] == 1
                assert float(row[2]) == float(1.2)
                assert ord(row[3]) == 0xff
            
            #test with argument list
            result2 = self.source.execute("SELECT %s,%s,%s,%s from dual", ('test', 1, 1.2, 0xff ))
            for row in result2:
                assert row[0] == 'test'
                assert row[1] == 1
                assert float(row[2]) == float(1.2)
                assert row[3] == 0xff

        finally:
            self.source.test_teardown_db()


    def test_crud(self):
        """
        Tests Create, Read, Update and Delete operations on this datasource.
        Not really an atomic test, but should do the job
        """

        self.source.test_setup_db()
        test_event = Event(message = "testmessage", additional = {
            "host_address" : ip_address.IPAddress("192.168.178.56"),
            "program" : "test_program"
        })
        try:
            # Create
            assert self.source.insert(test_event) == "OK"
            assert test_event["id"]
            
            # Read
            ev_from_db = self.source.get_event_by_id(test_event["id"])
            assert ev_from_db.message == "testmessage"
            assert ev_from_db["host_address"] == ip_address.IPAddress("192.168.178.56")
            assert ev_from_db["id"] == test_event["id"]
            
            # Update
            test_event["host_address"] = ip_address.IPAddress("192.168.178.57")
            test_event["message"] = "testmessage2"
            self.source.update(test_event)
            ev_from_db = self.source.get_event_by_id(test_event["id"])
            assert ev_from_db.message == "testmessage2"
            assert ev_from_db["host_address"] == ip_address.IPAddress("192.168.178.57")
            assert ev_from_db["id"] == test_event["id"]
            
            # Delete
            self.source.remove(test_event)
            ev_from_db = self.source.get_event_by_id(test_event["id"])
            assert ev_from_db == None
            
        finally:
            self.source.test_teardown_db()

    def test_message_overflow(self):
        """ Test what happens it the message is overflowing. This shouldn't break

        """
        try :
            self.source.test_setup_db()
            
            message = "test123456789"
            for i in range(0, 10):
                message += message;

            test_event = Event(message = message, additional = {
                "host_address" : ip_address.IPAddress("192.168.178.56"),
                "program" : "test_program"
            })
            self.source.insert(test_event)
            
            ev_from_db = self.source.get_event_by_id(test_event["id"])
            assert ev_from_db.message == message[0:4096] # assume data being truncated
        finally:
            self.source.test_teardown_db() 
        
    def test_group_implicit_insertion(self):
        """ Test implicit insertion to groups if an event matches them

        """
        try:
            self.source.test_setup_db()
            test_event = Event(message = "test", additional = {
                "host_address": ip_address.IPAddress("192.168.178.56"),
                "program" : "test_program",
                "priority" : 0,
                "facility" : 0,
                "active" : 1,
                "group_active" : True
            })
            test_event.group_leader = -1
            test_event.group_id = "test"
            self.source.insert(test_event)
            leader = self.source.get_group_leader("test")
            assert leader != (None, None)
            assert leader[0] == test_event["id"]
            lastmod = leader[1]
            time.sleep(1)
            
            # test moddate
            ev2 = Event(message = "test", additional = {
                "host_address" : ip_address.IPAddress("192.168.178.56"),
                "program" : "test_program",
                "priority" : 0,
                "facility" : 0,
                "active" : 1,
                "group_active" : True
            })
            ev2.group_leader = test_event["id"]
            ev2.group_id = "test"
            self.source.insert(ev2)
            
            leader = self.source.get_group_leader("test")
            assert leader != (None, None)
            assert leader[0] == test_event["id"]
            assert lastmod != leader[1]
            assert self.source.connections.qsize() == self.source.poolsize
            
        finally:
            self.source.test_teardown_db()


    def test_group_persistence(self):
        """ Tests whether grouped events are correctly persisted

        """

        try:
            self.source.test_setup_db()
            ev = Event(message="test", additional = {
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
            assert leader != (None, None)
            assert leader[0] == ev["id"]
            
            self.source.close()
            
            self.source = MysqlDatasource()
            self.source.setup("test", SETUP_DB)
            self.source.connect()
                        
            leader = self.source.get_group_leader("test\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
            assert leader != (None, None)
            assert leader[0] == ev["id"]            
            assert self.source.connections.qsize() == self.source.poolsize
            
        finally:
            self.source.test_teardown_db()
        


    def test_async_flush(self):
        """ Tests whether query buffering and buffer flushing is correctly working

        """
        try:
            self.source.test_setup_db()
            self.source.no_async_flush = False
            self.source.flush_interval = 500.0
            ev = Event(message="test", additional = {
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
        """ Removes any traces this test has left
        """
        try: 
            self.source.test_teardown_db()
        except:
            pass
        pass

    def test_mysql_gone_bug_2053(self):
        """
        Tests Create, Read, Update and Delete operations on this datasource.
        Not really an atomic test, but should do the job
        """

        try:
            self.source.test_setup_db()
            self.source.cursor_class = FailCursor
            test_event = Event(message = "testmessage", additional = {
                "host_address" : ip_address.IPAddress("192.168.178.56"),
                "program" : "test_program"
            })
            # Create
            assert self.source.insert(test_event) == "OK"
            assert test_event["id"]

            # Read
            ev_from_db = self.source.get_event_by_id(test_event["id"])
            assert ev_from_db.message == "testmessage"
            assert ev_from_db["host_address"] == ip_address.IPAddress("192.168.178.56")
            assert ev_from_db["id"] == test_event["id"]

        finally:
            self.source.test_teardown_db()

