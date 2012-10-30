'''
Pseudo persister that forfeits the event 
'''


class NullPersister(object):
    def setup(self,id,config):
        self.id = id
    
    def persist(self,event):
        return "OK"

    
