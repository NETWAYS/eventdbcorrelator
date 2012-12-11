import unittest

from datasource import MysqlDatasource, DBTransformer, SpoolDatasource
from event.event import *
import logging
from event import ip_address
from tests.mysql_datasource_test import SETUP_DB
import MySQLdb
import MySQLdb.cursors
import os 

TMP_DIR="/tmp/"
SPOOL_NAME="edbc_test.spool"

class NoOpCursorMock(object):
    def execute(self, query, args):
        raise MySQLdb.OperationalError("Mock throw object")

CURSOR_STATIC_HISTORY = []

class HistoryCursor(MySQLdb.cursors.Cursor):
    def __init__(self, connection):
        return MySQLdb.cursors.Cursor.__init__(self, connection)
    
    def execute(self, query, args):
        CURSOR_STATIC_HISTORY.append((query, args))
        return MySQLdb.cursors.Cursor.execute(self, query, args)
    

class MySQLDataSourceSpoolTest(unittest.TestCase):
    
    
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
  
    
    def test_buffered_outtake(self):
        try:
            self.source.test_setup_db()
            ds = SpoolDatasource()
            ds.setup("testspool",{
            
            })
            self.source.spool = ds
            cursor = NoOpCursorMock()
            self.source.execute("SELECT %s FROM DUAL",(1), cursor=cursor)
            self.source.execute("SELECT %s FROM DUAL",(2), cursor=cursor)
            self.source.execute("SELECT %s FROM DUAL",(3), cursor=cursor)
            self.source.execute("SELECT %s FROM DUAL",(4), cursor=cursor)
            
            assert len(self.source.spool.buffer)  > 0
            assert self.source.check_spool == True
            
            self.source.cursor_class = HistoryCursor
            self.source.execute("SELECT * FROM %s " % self.source.table)            
            assert self.source.check_spool == False
            assert len(self.source.spool.buffer) == 0
            assert len(CURSOR_STATIC_HISTORY) == 5
            
            
        finally:
            self.source.test_teardown_db()
            self.source.close(True)
            while CURSOR_STATIC_HISTORY:
                CURSOR_STATIC_HISTORY.pop()
    
    def clear_temp_files(self):
        try:
            os.unlink(TMP_DIR+SPOOL_NAME)
        except:
            pass        
    
    def test_flushed_outtake(self):
        try:
            self.clear_temp_files()
            self.source.test_setup_db()
            # test precondition
            assert not os.path.exists(TMP_DIR+SPOOL_NAME)
            ds = SpoolDatasource()
            ds.setup("testspool",{
                "spool_dir" : TMP_DIR,
                "spool_filename" : SPOOL_NAME
            })
            self.source.spool = ds
            

            
            cursor = NoOpCursorMock()
            self.source.execute("SELECT %s FROM DUAL",(5), cursor=cursor)
            self.source.execute("SELECT %s FROM DUAL",(6), cursor=cursor)
            self.source.execute("SELECT %s FROM DUAL",(7), cursor=cursor)
            self.source.execute("SELECT %s FROM DUAL",(8), cursor=cursor)
            ds.flush()
            assert len(ds.buffer) == 0
            assert self.source.check_spool == True
            
            self.source.cursor_class = HistoryCursor
            self.source.execute("SELECT * FROM %s " % self.source.table)            
            assert self.source.check_spool == False
            assert len(self.source.spool.buffer) == 0
            assert len(CURSOR_STATIC_HISTORY) == 5
            
            
        finally:
            self.clear_temp_files()
            try:
                self.source.test_teardown_db()
            except:
                pass
            self.source.close(True)

            while CURSOR_STATIC_HISTORY:
                CURSOR_STATIC_HISTORY.pop()
