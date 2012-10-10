'''
Pseudo persister that forfeits the event 
'''

from abstract_persister import AbstractPersister

class SqlPersister(AbstractPersister):
    def setup(self,id,config):
        self.id = id
        self.datasource = config["datasource"]
       
            
    def process(self,event):
        success = false
        if event["id"] != None:
            success = self.updateEvent(event)
        else:
            success = self.datasource.insertEvent(event)
                
        if success:
            return "OK"
        else:
            return "FAIL"

    
