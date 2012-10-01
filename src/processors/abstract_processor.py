

class AbstractProcessor(object):
    
    def setup(self,config):
        pass
    
    def registerController(self,controller):
        this.controller = controller
        
    def process(self,event):
        pass