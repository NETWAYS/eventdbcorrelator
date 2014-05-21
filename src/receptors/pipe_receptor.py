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
from abstract_receptor import AbstractReceptor;
import logging
import os
import pwd
import select
import Queue
from event import Event

class PipeReceptor(AbstractReceptor):
    """ Receptor that opens a pipe at a given location and reads events in a message
        format defined by the input formatter and transforms them to normalized Event 
        objects

    """   
    
 
    def setup(self, _id, config):
        """ Default setup method as called by the InstanceFactroy, sets up the pipe 
            but doesn't start the read operation yet

        """
        self.id = _id
        self.running = False
        self.callback = None
        self.iowait = 3
        self.config = {
            "mod" : 0666,
            "owner" : os.getuid(),
            "group" : os.getgid(),
            "path" : "/usr/local/var/edbc.pipe",
            "bufferSize" : 2048,
            "format" : None
        }
        
        self.run_flags = os.O_RDONLY|os.O_NONBLOCK
        for key in config.keys():
            if key == 'owner':
                config[key] = pwd.getpwnam(config[key]).pw_uid
            else:
                if key == 'group':
                    config[key] = pwd.getpwnam(config[key]).pw_gid
                else:
                    self.config[key] = config[key]
        if "source_type" in self.config:
            self.source = self.config["source_type"]
        else:
            self.source = "syslog"
        self.pipe = None
        self.queues = []
        self.setup_pipe()
     
    def start(self, queue=[], cb=None):
        """ Starts the receptor in a new thread
        
        """
        if not queue:
            queue = []
        if isinstance(queue, (list, tuple)):
            self.queues = queue
        else:
            self.queues = [queue]
        
        if cb != None:
            self.callback = cb
            
        if "noThread" in self.config: # this is only for testing
            #logging.debug("Threading disabled for PipeReceptor")
            return self.run()
        return super(PipeReceptor, self).start()
    
    
    def register_queue(self, queue):        
        """ Registers a queue to push new events to in the internal queue list

        """
        self.queues.append(queue)
    
    
    def unregister_queue(self, queue):
        """ Removes a queue from this receptors queue list

        """ 
        if queue in self.queues:
            self.queues.remove(queue)
    
    def _get_messages_from_raw_stream(self, data_packet):
        """ Reads mesages from raw string input and returns a list of messages 

        """
        if len(data_packet) == 0:
           return [] 
        messages = data_packet.split("\n")
        
        # ensure truncated messages not fitting in one buffer are respected
        if messages[0] == "":
            messages[0] = self.last_part
            self.last_part = ""
        if self.last_part != "" :
            messages[0] = self.last_part + messages[0]
            self.last_part = ""
        if data_packet[-1] != "\n":
            self.last_part = messages.pop()
        return messages
        
        
    def _read(self):
        """ Reads from the pipe and transforms raw event strings to normalized Event objecs

        """
        tr = self.config["transformer"]
        buffersize = self.config["bufferSize"]
        self.last_part = ""
        while self.running:
            try:
                inPipes, pout, pex = select.select([self.pipe], [], [], self.iowait)
            except Exception, exc:
                if self.running:
                    raise exc
                else:
                    return

            if len(inPipes) > 0:
                pipe = inPipes[0]
                try:
                    data_packet = os.read(pipe, buffersize)
                except OSError, e:
                    # EAGAIN means the pipe would block
                    # on reading, so try again later
                    if e.errno == 11:
                        logging.warning("would block on pipe read: %s" % self.id)
                        continue
                    else:
                        if not self.running:
                            return
                        raise e
                if len(data_packet) == 0:
                    # retry read in a bit
                    select.select([], [], [], self.iowait)
                    continue
                messages = self._get_messages_from_raw_stream(data_packet)

                for message in messages:                         
                    if message == "": 
                        continue
                    transformed = tr.transform(message)
                        
                    if self.queues and transformed:
                        if isinstance(transformed, Event):
                            transformed["source"] = self.source
                        for queue in self.queues:
                            queue.put(transformed)    
                    if self.callback != None:
                        self.callback(self, transformed)
                   
            else:
                if self.callback != None:
                    self.callback(self)
                continue
            if "noThread" in self.config:
                return
    
    def __reopen_pipe(self):
        """ If the pipe is closed, this method reopens it

        """
        try :
            if self.pipe != None:
                logging.warning("reopening pipe: %s" % self.id)
                os.close(self.pipe) 
        except OSError, e:
            pass
        
        self.pipe = os.open(self.config["path"], self.run_flags)
        
    def run(self):
        """ Thread entry method, calls __read()

        """
        try :
            self.__reopen_pipe()
            self.running = True
            self._read()
        finally:
            self.running = False
            logging.debug("Finished Receptor %s", self.id)
    
    def setup_pipe(self):
        """ Creates a new pipe according to the configuration of this receptor

        """
        #logging.debug("Setting up PipeReceptor with %s" % self.config)
        if os.path.exists(self.config["path"]):
            os.remove(self.config["path"])
        
        os.mkfifo(self.config["path"], int(self.config["mod"]))
        os.chown(self.config["path"], self.config["owner"], self.config["group"])
        os.chmod(self.config["path"], self.config["mod"])
        
    def __clean(self):
        """ Closes and removes the pipe

        """
        try:
            self.running = False
            os.close(self.pipe)
        except:
            pass
        if os.path.exists(self.config["path"]):
            os.remove(self.config["path"])
 
    def stop(self):
        """ Gracefully stops this receptor thread, closes the pipe and cleans up
    
        """
        try:
            logging.debug("Stopping Receptor %s ", self.id )
            if self.running == True:
                if os.path.exists(self.config["path"]):
                    fd = os.open(self.config["path"], os.O_WRONLY)
                    os.write(fd,"_")
                    self.running = False
                    os.close(fd)
                    
                self.__clean()
        finally:
            self.running = False        

        
