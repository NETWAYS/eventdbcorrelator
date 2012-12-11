
class NullProcessor(object):
    def setup(self,id,config = {}):
        self.id = id
        pass
    
    def process(self,event):
        return "OK"