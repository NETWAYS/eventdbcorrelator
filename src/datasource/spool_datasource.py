
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
import threading
import pickle
import os
from collections import deque 

class SpoolDatasource(object):
    """ Spool datasource that supports the primary datasource if it's not available
        and caches events until it is backup. Can cache in memory or flush cache to persistent spool
        files. Can't be used as the primary database. 

    """
   
 
    def setup(self, _id, config):
        """ Setup method that configures the instance of this method

        InstanceFactory calls this with the id and configuration from datasource
        definitions defined in the conf.d directory
        """
        self.id = _id
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
        """ Fake cursor implementation, just returns the spool instance itself
        
        """
        return self
    
    def close(self):
        """ Fake close method
        """
        pass
    
    def open(self):
        """ Fake open method
        """
        pass
    
    def execute(self, query, args = (), noResult=False, cursor=None):
        """ Executes the query, i.e. writes it to spool
        
        """ 
        try:
            self.lock.acquire()
            self.write_to_spool(query, args)
            return None
        finally:
            self.lock.release()
    
    def commit(self):
        """ Fake commit method

        """
        pass
    
    def open_spool_handler(self):
        """ Opens the spool file 

        """
        if not os.access(self.spool_dir, os.W_OK | os.R_OK):
            raise Exception("Spool dir %s is not write and readable" % self.spool_dir)
        self.spool_handle = open(self.spool_dir+"/"+self.spool_filename,"a+")
        
    def _flush_buffer_to_file(self, clear = False):
        """ Flushes the spool buffer from the memory to a file 

        """
        if not self.spool_handle:
            self.buffer.popleft() # if no flush is possible, pop one item so we have space
            return 
        
        while self.buffer:
            item = self.buffer.popleft()
            item_str = pickle.dumps(item)
            
            self.spool_handle.write(item_str+"\n")
        self.spool_handle.flush()
    
    def flush(self):
        """ Flushes the spool. If a file is given, the memory is flushed to file, otherwise
            the buffer is just truncated 

        """
        try:
            self.lock.acquire()
            self._flush_buffer_to_file()
        finally:
            self.lock.release()
    
    def get_spool_from_file(self):
        """ Returns the spooled queries from file

        """
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
    
    def write_to_spool(self, query, args):
        """ Writes the query to the spool

        """
        if len(self.buffer) >= self.spool_buffer_size:
            self._flush_buffer_to_file()
        
        self.buffer.append((query, args))
        
    def get_spooled(self):
        """ Returns the currently spooled entries (From file or memory)

        """
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
        """ Does nothing, fake cursor operation

        """
        return ()
