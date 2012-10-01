from abstract_processor import AbstractProcessor
import logging

class AggregationProcessor(AbstractProcessor):
    def setup(self,id,config = {}):
        self.id = id
        self.options = {
            "clear": None,                  # DEFAULT: No clear message 
            "match": "(@message=\"(?P<MSG>.*\")",   # DEFAULT: Match same message
            "maxDelay": 600,                # DEFAULT: Break aggregation when 
                                            # 10 minutes have passed without matching event
            "maxCount": -1,                 # DEFAULT: No limit in how many events can be aggregated
            "correlateMessage": "$MSG ($COUNT)",
            "datasource": None             
        }
        if "clear" in config:
            self.clear = config.clear

    def process(self,event):
        pass