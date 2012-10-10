import unittest
import os

from datasource import SpoolDatasource
TMP_DIR="/tmp/"
SPOOL_NAME="edbc_test.spool"



class SpoolDatasourceTest(unittest.TestCase):
    def clear_temp_files(self):
        try:
            os.unlink(TMP_DIR+SPOOL_NAME)
        except:
            pass
        
    def test_spool_file_creation(self):
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
        try:
            ds = SpoolDatasource()
            ds.setup("test",{
                "buffer_size" : 10
            })
            cursor = ds.cursor()
            for i in range(0,100):
                ds.execute(i,i)
            ds.close()
            assert len(ds.buffer) == 10
            i = 90
            for x in ds.buffer:
                assert x == (i,i)
                i = i+1
            
            
        finally:
            self.clear_temp_files()
    
    def test_spool_buffer_in_file(self):
        try:
            ds = SpoolDatasource()
            ds.setup("test",{
                "buffer_size" : 10,
                "spool_dir" : TMP_DIR,
                "spool_filename" : SPOOL_NAME
            })
            cursor = ds.cursor()
            for i in range(0,10):
                ds.execute(i,i)
            
            assert len(ds.buffer) == 10
            ds.execute(11,11)
            assert len(ds.buffer) == 1
            assert ds.buffer[0] == (11,11)
        
        finally:
            self.clear_temp_files()
    
    def test_spool_memory_get_content(self):
            ds = SpoolDatasource()
            ds.setup("test",{
                "buffer_size" : 10
            })
            cursor = ds.cursor()
            for i in range(0,100):
                cursor.execute(i,i)
            ds.close()
            result = ds.get_spooled()
            # Assert everything exceeding the buffer size being truncated
            assert len(result) == 10
            pos = 90
            for i in result:
                assert i[0] == pos
                pos = pos+1
                
    def test_spool_file_get_content(self):
        ds = SpoolDatasource()
        ds.setup("test",{
            "buffer_size" : 10,
            "spool_dir" : TMP_DIR,
            "spool_filename" : SPOOL_NAME            
        })
        cursor = ds.cursor()
        for i in range(0,100):
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


    def tearDown(self):
        self.clear_temp_files()