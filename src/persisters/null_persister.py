'''
Pseudo persister that forfeits the event 
'''

from abstract_persister import AbstractPersister

class NullPersister(AbstractPersister):
    def setup(self,id,config):
        self.id = id
    
    def persist(self,event):
        pass

    
