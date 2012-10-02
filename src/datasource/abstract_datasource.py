
class AbstractDatasource(object):
    def setup(self,config):
        pass
        
    def connect(self):
        pass
    def is_available(self):
        pass
    def insert(self,event):
        pass
    def remove(self,event):
        pass
    def update(self,event):
        pass
        
    def execute(self,query,args):
        pass
    
    def close(self):
        pass