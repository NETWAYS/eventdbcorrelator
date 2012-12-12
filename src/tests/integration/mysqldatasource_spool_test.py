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
import MySQLdb
import MySQLdb.cursors
import os 
import logging

from datasource import MysqlDatasource, DBTransformer, SpoolDatasource
from event.event import Event, Matcher
from event import ip_address
from tests.mysql_datasource_test import SETUP_DB

TMP_DIR = "/tmp/"
SPOOL_NAME=  "edbc_test.spool"
CURSOR_STATIC_HISTORY = []

class NoOpCursorMock(object):
    """ Cursor mock that does nothing but throws an error on exec
        
    """


    def execute(self, query, args):
        """ Raises an MySQLdb.OperationalError

        """
        raise MySQLdb.OperationalError("Mock throw object")


class HistoryCursor(MySQLdb.cursors.Cursor):
    """ Cursor mock that adds all queries to the static, package global list CURSOR_STATIC_HISTORY
        Used to see what would have been written to the database
    """


    def __init__(self, connection):
        MySQLdb.cursors.Cursor.__init__(self, connection)
    
    def execute(self, query, args):
        """ Appends query and args as a tuple to CURSOR_STATIC_HISTORY

        """
        CURSOR_STATIC_HISTORY.append((query, args))
        return MySQLdb.cursors.Cursor.execute(self, query, args)
    

class MySQLDataSourceSpoolTest(unittest.TestCase):
    """ Integration test for MySQLDataSource and SpoolDatasource 
        Checks if upon mysql errors queries are logged to the spool

    """ 
    
    def setUp(self):
        """ Setup for the test, creates the initial DB
            
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
  
    
    def test_buffered_outtake(self):
        """ Checks if queries are correctly buffered on issues and rewritten
            to the db as soon as it's available again
        """
        try:
            self.source.test_setup_db()
            ds = SpoolDatasource()
            ds.setup("testspool", {
            })
            self.source.spool = ds
            # NoOpCursorMock always crashes on execute, so the next queries are 
            # hopefully written to spool 
            cursor = NoOpCursorMock()
            self.source.execute("SELECT %s FROM DUAL", (1), cursor=cursor)
            self.source.execute("SELECT %s FROM DUAL", (2), cursor=cursor)
            self.source.execute("SELECT %s FROM DUAL", (3), cursor=cursor)
            self.source.execute("SELECT %s FROM DUAL", (4), cursor=cursor)
            
            # Test if the spool contains data
            assert len(self.source.spool.buffer)  > 0
            assert self.source.check_spool == True
            
            # Now use a working cursor
            self.source.cursor_class = HistoryCursor
            self.source.execute("SELECT * FROM %s " % self.source.table)

            # Check if the spool is empty and if there are 5 entries in the DB history
            assert self.source.check_spool == False
            assert len(self.source.spool.buffer) == 0
            assert len(CURSOR_STATIC_HISTORY) == 5
            
        finally:
            self.source.test_teardown_db()
            self.source.close(True)
            while CURSOR_STATIC_HISTORY:
                CURSOR_STATIC_HISTORY.pop()
    
    def clear_temp_files(self):
        """ removes temporary files, i.e. the spool
            
        """
        try:
            os.unlink(TMP_DIR+SPOOL_NAME)
        except:
            pass        
    
    def test_flushed_outtake(self):
        """ Test if the spool writes correctly to the db after it's contents
            have been flushed to a file
        """
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
            self.source.execute("SELECT %s FROM DUAL", (5), cursor=cursor)
            self.source.execute("SELECT %s FROM DUAL", (6), cursor=cursor)
            self.source.execute("SELECT %s FROM DUAL", (7), cursor=cursor)
            self.source.execute("SELECT %s FROM DUAL", (8), cursor=cursor)
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
