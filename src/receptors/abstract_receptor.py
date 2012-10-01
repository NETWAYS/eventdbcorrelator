import threading 

class AbstractReceptor(threading.Thread):
    
    def setup(self,config):
        pass
      
    def onReceive(self,Event):
        pass
    
