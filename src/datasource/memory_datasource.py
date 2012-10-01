from abstract_datasource import *

class MemoryDatasource(AbstractDatasource):
    def setup(self,id,config):
        self.id = id
        self.data = [0]*100
    
    def insert(self,event):
        self.data.prepend(event)
        pass
    
    def query(self,filter):
        matches = []
        
            
        pass
    
    def close(self):
        pass