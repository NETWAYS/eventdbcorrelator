# To change this template, choose Tools | Templates
# and open the template in the editor.
from abstract_receptor import AbstractReceptor;
import logging
import os
import pwd
import select
import Queue

class PipeReceptor(AbstractReceptor):
    
    def setup(self,id,config):
        self.id = id
        self.running = False
        self.callback = None
        self.config = {
            "mod": 0666,
            "owner": os.getuid(),
            "group": os.getgid(),
            "path" : "/tmp/edbc.pipe",
            "bufferSize" : 2048,
            "format" : None
        }
        self.runFlags = os.O_RDONLY|os.O_NONBLOCK
        for key in config.keys():
            if key == 'owner':
                config[key] = pwd.getpwnam(config[key]).pw_uid
            else:
                if key == 'group':
                    config[key] = pwd.getpwnam(config[key]).pw_gid
                else:
                    self.config[key] = config[key]
        
        self.pipe = None
        self.queues = []
        self.__setup_pipe()
    
    
    
    def start(self,queue=[],cb=None):
        if isinstance(queue, (list, tuple)):
            self.queues = queue
        else:
            self.queues = [queue]
        
        if cb != None:
            self.callback = cb
            
        if "noThread" in self.config: # this is only for testing
            #logging.debug("Threading disabled for PipeReceptor")
            return self.run()
        return super(PipeReceptor,self).start()
    
    
    def register_queue(self,queue):
        self.queues.append(queue)
    
    def unregister_queue(self,queue):
        self.queues.remove(queue)
    
    def __get_messages_from_raw_stream(self,dataPacket):
        if len(dataPacket) == 0:
           return [] 
        messages = dataPacket.split("\n")
        
        # ensure truncated messages not fitting in one buffer are respected
        if messages[0] == "":
            messages[0] = self.lastPart
            self.lastPart = ""
        if self.lastPart != "" :
            messages[0] = self.lastPart + messages[0]
            self.lastPart = ""
        if dataPacket[-1] != "\n":
            self.lastPart = messages.pop()
        return messages
        
        
    def __read(self):
        tr = self.config["transformer"]
        buffersize = self.config["bufferSize"]
        pipe = None
        self.lastPart = ""
        while self.running:
            inPipes,pout,pex = select.select([self.pipe],[],[],3)

            if len(inPipes) > 0:
                pipe = inPipes[0]
                dataPacket = os.read(pipe,buffersize)
                if len(dataPacket) == 0:
                    self.__reopen_pipe()
                    continue
                messages = self.__get_messages_from_raw_stream(dataPacket)
                
                for message in messages:                         
                    if message == "": 
                        continue
                    transformed = tr.transform(message)
                    if self.queues:
                        for queue in self.queues:
                            queue.put(transformed)    
                    if self.callback != None:
                        self.callback(self,transformed)
                   
            else:
                if self.callback != None:
                    self.callback(self)
                continue
            if "noThread" in self.config:
                return
    
    def __reopen_pipe(self):
        try :
            if self.pipe != None:
                os.close(self.pipe) 
        except OSError,e:
            pass
        
        self.pipe = os.open(self.config["path"],self.runFlags)
        
    def run(self):
        try :
            self.__reopen_pipe()
            self.running = True
            try :                
                self.__read()
            except OSError, e:
                logging.warn("Error %s", e)
            self.running = False

        finally:
            logging.debug("Finished PipeReceptor %s", self.id)
    
    def __setup_pipe(self):
        #logging.debug("Setting up PipeReceptor with %s" % self.config)
        if os.path.exists(self.config["path"]):
            os.remove(self.config["path"])
        
        os.mkfifo(self.config["path"],int(self.config["mod"]))
        os.chown(self.config["path"],self.config["owner"],self.config["group"])
        
        
    def __clean(self):
        try: 
            os.close(self.pipe)
        except:
            pass
        if os.path.exists(self.config["path"]):
            os.remove(self.config["path"])

    
    def on_receive(self,Event):
        pass
    
    def stop(self):
        try:
            logging.debug("Stopping PipeReceptor %s " % self.id )
            if self.running == True:
                if os.path.exists(self.config["path"]):
                    fd = os.open(self.config["path"],os.O_WRONLY)
                    os.write(fd,"_")
                    os.close(fd)
                    
                self.__clean()
        finally:
            self.running = False        

        
