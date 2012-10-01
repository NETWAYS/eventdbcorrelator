# Abstract persister class 
# and open the template in the editor.

class AbstractPersister(object):
    def setup(self,id,config):
        raise NotImplementedError()
    
    def persist(self,event):
        raise NotImplementedError()
    
    def registerController(self,controller):
        this.controller = controller
