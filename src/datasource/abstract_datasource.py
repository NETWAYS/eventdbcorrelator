
class AbstractDatasource(object):
    def connect(self,config):
        pass
    
    def insert(self,event):
        pass
    
    def query(self,query,args):
        pass
    
    def close(self):
        pass