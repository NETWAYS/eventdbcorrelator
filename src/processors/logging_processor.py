'''
Simple processor that only logs to stdout
'''

import logging

class LoggingProcessor(object):
    
    def setup(self,id,config):
        self.id = id
        pass
    
    def process(self,event):
        logging.debug("Event : msg=%s host=%s host_addr=%s prio:%s facility:%s " % (event["message"],event["host"],event["host_address"],event["priority"],event["facility"]))
        