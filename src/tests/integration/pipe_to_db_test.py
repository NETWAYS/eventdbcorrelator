import unittest
from datasource import MysqlDatasource, DBTransformer
from event.event import *
import logging
from event import ip_address
from tests.mysql_datasource_test import SETUP_DB
import MySQLdb
import MySQLdb.cursors
import os 




class PipeToDBTest(unittest.TestCase):
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
        
    def testSinglePipeSingleDB(self):
        try:
            self.source.test_setup_db()
            self
        finally:
            self.source.test_teardown_db()
            self.source.close(True)
    
