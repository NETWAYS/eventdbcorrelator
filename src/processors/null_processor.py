from abstract_processor import AbstractProcessor

class NullProcessor(AbstractProcessor):
    def setup(self,id,config = {}):
        self.id = id
        pass
    
    def process(self,event):
        return event