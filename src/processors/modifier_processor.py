

import logging
from event import Matcher,TrueMatcher
MOD_TARGETS = ["event","group"]

class ModifierProcessor(object):
    
    def setup(self,id,config):
        self.id = id
        self.overwrites = []
        if "overwrite" in config:
            overwrite_keyvals = config["overwrite"].split(";")
            for keyval in overwrite_keyvals:
                self.overwrites.append(keyval.split("="))
        self.target = "event"
        if "target" in config:
            if not config["target"] in MOD_TARGETS:
                logging.warn("Target %s is invalid for ModifierProcessor %s, using 'event' instead" % (config["target"],self.id))
            else:
                self.target = config["target"]
        
        self.datasource = None
        if "datasource" in config:
            self.datasource = config["datasource"]
                
        self.acknowledge = False
        
        self.matcher = TrueMatcher()
        if "matcher" in config:
            self.matcher = Matcher(config["matcher"])
            
        if "acknowledge" in config:
            if config["acknowledge"] != "false":
                self.acknowledge = True
        
    def process(self,event):
        if not self.matcher.matches(event):
            return "PASS"
        logging.debug("processing ...")
        if self.target == "event":
            return self.process_event(event)
        if self.target == "group" and event["group_id"] or event["clear_group_id"]:
            return self.process_group(event)
        
    def process_event(self,event):
        if self.acknowledge:
            event["ack"] = 1
        for (key,val) in self.overwrites:
            event[key] = val
        return "OK"
    
    def process_group(self,event):
        if not self.datasource :
            logging.warn("Can't process group without datasource")
            return "PASS"
        query = "UPDATE "+self.datasource.table+" SET "
        glue = ""
        if self.acknowledge:
            query = query+" ack = 1 "
            glue = ","
        
        for (key,val) in self.overwrites:            
            query = query + "%s %s = '%s' " % (glue,key,val,)
            glue = ","
        group_id = event["group_id"] or event["clear_group_id"]
        group_leader = event["group_leader"] or event["clear_group_leader"]
        query = query + " WHERE (group_id = '%s' AND group_leader = '%s') OR id='%s' " % (group_id,group_leader,group_leader)
        self.datasource.execute_after_flush(query)
        return "OK"