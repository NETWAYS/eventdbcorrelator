import logging

class SqlPersister(object):
    def setup(self,id,config):
        self.id = id
        self.datasource = config["datasource"]
       
            
    def process(self,event):
        logging.debug("Inserting %s" % event)
        return self.datasource.insert(event)
    