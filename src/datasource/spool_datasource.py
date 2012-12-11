
import threading
import pickle
import os
from collections import deque 

class SpoolDatasource(object):
    
    def setup(self,id,config):
        self.id = id
        self.spool_filename = "edbc.spool"
        
        if "spool_filename" in config:
            self.spool_filename = config["spool_filename"]
            
        if "spool_dir" in config:
            self.spool_dir = config["spool_dir"]
            self.open_spool_handler()
            
        else:
            self.spool_dir = None
            self.spool_handle = None
        self.lock = threading.Lock()
        
        self.spool_buffer_size = 1000
        if "buffer_size" in config:
            self.spool_buffer_size = config["buffer_size"]
        
        # Omitting maxlen because of python 2.4 support...
        self.buffer = deque()
        self.open = True
        self.is_spool = False
        
    def cursor(self):
        return self
    
    def close(self):
        pass
    
    def open(self):
        pass
    
    def execute(self,query,args = (),noResult=False,cursor=None):
        try:
            self.lock.acquire()
            self.write_to_spool(query,args)
            return None
        finally:
            self.lock.release()
    
    def commit(self):
        pass
    
    def open_spool_handler(self):
        if not os.access(self.spool_dir, os.W_OK|os.R_OK):
            raise Exception("Spool dir %s is not write and readable" % self.spool_dir)
        self.spool_handle = open(self.spool_dir+"/"+self.spool_filename,"a+")
        
    # protected, as this requires an acquired lock
    def _flush_buffer_to_file(self,clear = False):
        if not self.spool_handle:
            self.buffer.popleft() # if no flush is possible, pop one item so we have space
            return 
        
        while self.buffer:
            item = self.buffer.popleft()
            item_str = pickle.dumps(item)
            
            self.spool_handle.write(item_str+"\n")
        self.spool_handle.flush()
    
    def flush(self):
        try:
            self.lock.acquire()
            self._flush_buffer_to_file()
        finally:
            self.lock.release()
    
    def get_spool_from_file(self):
        if not self.spool_handle:
            return []
        buf = ""
        result = []
        self.spool_handle.seek(0)
        for line in self.spool_handle:
            buf = buf+line
            if line.endswith(".\n"):
                result.append(pickle.loads(buf))
                buf = ""
        os.unlink(self.spool_dir+"/"+self.spool_filename)
        self.spool_handle.close()
        self.open_spool_handler()
        return result
        
        
    
    def write_to_spool(self,query,args):
        if len(self.buffer) >= self.spool_buffer_size:
            self._flush_buffer_to_file()
        
        self.buffer.append((query,args))
        
    def get_spooled(self):
        try:
            self.lock.acquire()
            result = self.get_spool_from_file()
            for i in self.buffer:
                result.append(i)

            return result
        finally:
            self.buffer.clear()
            self.lock.release()
    
    def fetchall(self):
        return ()