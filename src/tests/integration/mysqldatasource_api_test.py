import unittest
import socket
import pickle
import os
import time

from receptors.checkapi_receptor import CheckapiReceptor
from datasource import MysqlDatasource
from event import Event
from network import ip_address
from tests.mysql_datasource_test import SETUP_DB, DBTransformerMock

CURSOR_STATIC_HISTORY = []
SOCK_LOCATION = "/tmp/test_api_edbc.sock"


class MySQLDatasourceApiTest(unittest.TestCase):

    def setUp(self):
        """ Setup for the test, creates the initial DB

        """
        self.source = MysqlDatasource()
        dbsetup = SETUP_DB
        dbsetup["transform"] = DBTransformerMock()
        self.api = CheckapiReceptor()
        self.api.setup("testapi",{
            "path"        : SOCK_LOCATION,
            "datasource"  : self.source
        })
        self.source.setup("test", dbsetup)

        # Try tearing down the database in case a previous run ran wihtou cleanup
        try:
            self.source.test_teardown_db()
            self.source.close(True)
        except:
            pass

    def startup(self):
        self.started = True
        self.source.test_setup_db()
        self.populate_db()
        self.api.start()
        self.assertTrue(os.path.exists(SOCK_LOCATION))


    def shutdown(self):
        try:
            if self.started:
                self.started = False
                self.api.stop()
        finally:
            self.source.test_teardown_db()
            self.cleanPaths()

    def test_setup(self):
        try:
            self.startup()
        finally:
            self.shutdown()

    def get_api_connection(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(SOCK_LOCATION)
        return sock


    def test_simple_query(self):
        try:
            self.startup()
            conn = self.get_api_connection();
            conn.send("startfrom=0")
            result = pickle.loads(conn.recv(4096))
            self.api.stop()

            self.assertEquals(6, result["total"])
            self.assertEquals(6, result["last_id"])
            self.assertEquals(6, result["nr_of_warnings"])
            self.assertEquals(6, result["nr_of_criticals"])

        finally:
            self.shutdown()

    def test_offset_query(self):
        try:
            self.startup()
            conn = self.get_api_connection();
            conn.send("startfrom=3")
            result = pickle.loads(conn.recv(4096))
            self.api.stop()

            self.assertEquals(3, result["total"])
            self.assertEquals(6, result["last_id"])
            self.assertEquals(3, result["nr_of_warnings"])
            self.assertEquals(3, result["nr_of_criticals"])
        finally:
            self.shutdown()

    def test_host_filter_query(self):
        try:
            self.startup()
            conn = self.get_api_connection();
            conn.send("startfrom=0&host=hosta")
            result = pickle.loads(conn.recv(4096))
            self.api.stop()

            self.assertEquals(4, result["total"])
            self.assertEquals(4, result["last_id"])
            self.assertEquals(4, result["nr_of_warnings"])
            self.assertEquals(4, result["nr_of_criticals"])
        finally:
            self.shutdown()

    def test_host_filter_wildcard_query(self):
        try:
            self.startup()
            conn = self.get_api_connection();
            conn.send("startfrom=0&host=%a")
            result = pickle.loads(conn.recv(4096))
            self.api.stop()

            self.assertEquals(4, result["total"])
            self.assertEquals(4, result["last_id"])
            self.assertEquals(4, result["nr_of_warnings"])
            self.assertEquals(4, result["nr_of_criticals"])
        finally:
            self.shutdown()

    def test_host_severity_distinguish(self):
        try:
            self.startup()
            conn = self.get_api_connection();
            conn.send("startfrom=0&prio_warning=1,2,3&prio_critical=5")
            result = pickle.loads(conn.recv(4096))
            self.api.stop()

            self.assertEquals(6, result["total"])
            self.assertEquals(6, result["last_id"])
            self.assertEquals(3, result["nr_of_warnings"])
            self.assertEquals(1, result["nr_of_criticals"])
        finally:
            self.shutdown()

    def test_priority_filter(self):
        try:
            self.startup()
            conn = self.get_api_connection();
            conn.send("startfrom=0&priority=1,2,6")
            result = pickle.loads(conn.recv(4096))
            self.api.stop()

            self.assertEquals(3, result["total"])
            self.assertEquals(6, result["last_id"])
            self.assertEquals(3, result["nr_of_warnings"])
            self.assertEquals(3, result["nr_of_criticals"])
        finally:
            self.shutdown()

    def test_facility_filter(self):
        try:
            self.startup()
            conn = self.get_api_connection();
            conn.send("startfrom=0&facility=1,2,6")
            result = pickle.loads(conn.recv(4096))
            self.api.stop()

            self.assertEquals(3, result["total"])
            self.assertEquals(6, result["last_id"])
            self.assertEquals(3, result["nr_of_warnings"])
            self.assertEquals(3, result["nr_of_criticals"])
        finally:
            self.shutdown()

    def test_max_age_filter(self):
        try:
            self.startup()
            conn = self.get_api_connection();
            now = int(time.mktime(time.localtime()))
            conn.send("startfrom=0&maxage="+str(now))
            result = pickle.loads(conn.recv(4096))

            self.assertEquals(6, result["total"])
            self.assertEquals(6, result["last_id"])
            self.assertEquals(6, result["nr_of_warnings"])
            self.assertEquals(6, result["nr_of_criticals"])
            conn.close()

            conn = self.get_api_connection();
            conn.send("startfrom=0&maxage="+str(now+1000))
            result = pickle.loads(conn.recv(4096))

            self.assertEquals(0, result["total"])
            self.assertEquals(None, result["last_id"])
            self.assertEquals(0, result["nr_of_warnings"])
            self.assertEquals(0, result["nr_of_criticals"])


        finally:
            self.shutdown()

    def test_ip_filter(self):
        try:
            self.startup()
            conn = self.get_api_connection();
            conn.send("startfrom=0&ipaddress=192.168.178.56")
            result = pickle.loads(conn.recv(4096))

            self.assertEquals(4, result["total"])
            self.assertEquals(4, result["last_id"])
            self.assertEquals(4, result["nr_of_warnings"])
            self.assertEquals(4, result["nr_of_criticals"])

            conn = self.get_api_connection();
            conn.send("startfrom=0&ipaddress=192.168.178.59")
            result = pickle.loads(conn.recv(4096))

            self.assertEquals(2, result["total"])
            self.assertEquals(6, result["last_id"])
            self.assertEquals(2, result["nr_of_warnings"])
            self.assertEquals(2, result["nr_of_criticals"])


        finally:
            self.shutdown()

    def test_program_filter(self):
        try:
            self.startup()
            conn = self.get_api_connection();
            conn.send("startfrom=0&program=test_program")
            result = pickle.loads(conn.recv(4096))

            self.assertEquals(2, result["total"])
            self.assertEquals(2, result["last_id"])
            self.assertEquals(2, result["nr_of_warnings"])
            self.assertEquals(2, result["nr_of_criticals"])

            conn = self.get_api_connection();
            conn.send("startfrom=0&program=test_program2")

            result = pickle.loads(conn.recv(4096))

            self.assertEquals(4, result["total"])
            self.assertEquals(6, result["last_id"])
            self.assertEquals(4, result["nr_of_warnings"])
            self.assertEquals(4, result["nr_of_criticals"])

            conn = self.get_api_connection();
            conn.send("startfrom=0&program=test_program2,test_program")

            result = pickle.loads(conn.recv(4096))

            self.assertEquals(6, result["total"])
            self.assertEquals(6, result["last_id"])
            self.assertEquals(6, result["nr_of_warnings"])
            self.assertEquals(6, result["nr_of_criticals"])

        finally:
            self.shutdown()


    def cleanPaths(self):
        try:
            os.path.unlink(SOCK_LOCATION)
        except:
            pass


    def populate_db(self):
        events = [Event(message = "testmessage", additional = {
                "host_name" : "hosta",
                "host_address" : ip_address.IPAddress("192.168.178.56"),
                "program" : "test_program",
                "priority" : 1,
                "facility" : 6,
                "created" : time.localtime()
            }), Event(message = "testmessage2", additional = {
                "host_name" : "hosta",
                "host_address" : ip_address.IPAddress("192.168.178.56"),
                "program" : "test_program",
                "priority" : 2,
                "facility" : 5,
                "created" : time.localtime()
            }),Event(message = "testmessage", additional = {
                "host_name" : "hosta",
                "host_address" : ip_address.IPAddress("192.168.178.56"),
                "program" : "test_program2",
                "priority" : 3,
                "facility" : 4,
                "created" : time.localtime()
            }),Event(message = "testmessage6", additional = {
                "host_name" : "hosta",
                "host_address" : ip_address.IPAddress("192.168.178.56"),
                "program" : "test_program2",
                "ack" : 1,
                "priority" : 4,
                "facility" : 3,
                "created" : time.localtime()
            }),Event(message = "testmessage5", additional = {
                "host_name" : "hostb",
                "host_address" : ip_address.IPAddress("192.168.178.59"),
                "program" : "test_program2",
                "priority" : 5,
                "facility" : 2,
                "created" : time.localtime()
            }),Event(message = "testmessage4", additional = {
                "host_name" : "hostc",
                "host_address" : ip_address.IPAddress("192.168.178.59"),
                "program" : "test_program2",
                "priority" : 6,
                "facility" : 1,
                "created" : time.localtime()
            })]
        for event in events:
            self.source.insert(event)