'''
Pseudo persister that forfeits the event 
'''

from abstract_persister import AbstractPersister

class SqlPersister(AbstractPersister):
    def setup(self,id,config):
        self.id = id
        self.datasource = config["datasource"]
        if "spool" in config:
            self.spool = config["spool"]
        else:
            self.spool = None
            
    def process(self,event):
        if not self.datasource.available() and self.spool:
            self.spool.persist(event)
            return "not_available"
            
        success = false
        if event["db_primary_id"] != None:
            success = self.updateEvent(event)
        else:
            if event["is_phantom"] == True:
                success = self.removeEvent(event)
            else: 
                success = self.datasource.insertEvent(event)
                
        if success:
            return "ok"
        else:
            return "fail"

    
