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
import os

from datasource import SpoolDatasource
TMP_DIR = "/tmp/"
SPOOL_NAME = "edbc_test.spool"


class SpoolDatasourceTest(unittest.TestCase):
    """ Test cases for the spool datasource which provides
        query backup in case the db is gone away

    """


    def clear_temp_files(self):
        """ Helper method to clean previous existing test spool
            files
        """
        try:
            os.unlink(TMP_DIR+SPOOL_NAME)
        except:
            pass
        
    def test_spool_file_creation(self):
        """ Tests if SpoolDatasource creates the spool files
            upon initialization (which is NOT __init__ but setup)
        """
        try:
            ds = SpoolDatasource()
            ds.setup("test",{
                "spool_dir" : TMP_DIR,
                "spool_filename" : SPOOL_NAME
            })
            assert os.path.exists(TMP_DIR+SPOOL_NAME)
            ds.close()
        finally:
            self.clear_temp_files()
    
    def test_spool_buffer_in_memory(self):
        """ Test spooling of queries in memory 

        """
        try:
            ds = SpoolDatasource()
            ds.setup("test",{
                "buffer_size" : 10
            })
            cursor = ds.cursor()
            for i in range(0, 100):
                ds.execute(i, i)
            ds.close()
            assert len(ds.buffer) == 10
            i = 90
            for x in ds.buffer:
                assert x == (i, i)
                i = i+1
        finally:
            self.clear_temp_files()
   
 
    def test_spool_buffer_in_file(self):
        """ Test spooling of queries in spool files

        """
        try:
            ds = SpoolDatasource()
            ds.setup("test",{
                "buffer_size" : 10,
                "spool_dir" : TMP_DIR,
                "spool_filename" : SPOOL_NAME
            })
            cursor = ds.cursor()
            for i in range(0, 10):
                ds.execute(i, i)
            
            assert len(ds.buffer) == 10
            ds.execute(11, 11)
            assert len(ds.buffer) == 1
            assert ds.buffer[0] == (11, 11)
        
        finally:
            self.clear_temp_files()
    
    def test_spool_memory_get_content(self):
        """ Test spool memory content access

        """
        try:
            ds = SpoolDatasource()
            ds.setup("test",{
                "buffer_size" : 10
            })
            cursor = ds.cursor()
            for i in range(0, 100):
                cursor.execute(i, i)
            ds.close()
            result = ds.get_spooled()
            # Assert everything exceeding the buffer size being truncated
            assert len(result) == 10
            pos = 90
            for i in result:
                assert i[0] == pos
                pos = pos+1
        finally:
            self.clear_temp_files()
       
    def test_spool_file_get_content(self):
        """ Test spool access from spool files

        """
        try:
            ds = SpoolDatasource()
            ds.setup("test",{
                "buffer_size" : 10,
                "spool_dir" : TMP_DIR,
                "spool_filename" : SPOOL_NAME            
            })
            cursor = ds.cursor()
            for i in range(0, 100):
                cursor.execute(i,"test\ntest\n.\n")
            ds.close()
            result = ds.get_spooled()

            assert len(result) == 100
            pos = 0
            for i in result:
                assert i[0] == pos
                assert i[1] == "test\ntest\n.\n"
                pos = pos+1
            result = ds.get_spooled()
            assert len(result) == 0
        finally: 
            self.clear_temp_files()
            
    def tearDown(self):
        """ Cleanup when done testing

        """
        self.clear_temp_files()
