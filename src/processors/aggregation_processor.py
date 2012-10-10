USE_DEPRECATED_MD5 = False
try: 
    from hashlib import md5
except ImportError:
    from md5 import md5
    USE_DEPRECATED_MD5 = True

import threading
import re
import logging
import time

from abstract_processor import AbstractProcessor
from event import matcher


DB_TYPE_AGGREGATION_GROUP = 1


class AggregationProcessor(AbstractProcessor):
    
    
    def setup(self,id,config = {}):
        self.id = id
        self.config = {
            "maxDelay": 600,             # DEFAULT: Break aggregation when 
                                         # 10 minutes have passed without matching event
            "maxCount": -1,              # DEFAULT: No limit in how many events can be aggregated
            "datasource": None,
            "aggregateMessage": "Got : #message results"
        }
        
        for i in config:
            self.config[i] = config[i]
        self.validate()
        self.lock = threading.Lock()
        self.datasource = self.config["datasource"]
        self.create_matcher()
    
    
    def validate(self):
        if not self.config["datasource"]:
            raise Exception("No datasource given to Aggregator %s" % self.id)
 
 
    def process(self,event):
        matchgroups = {}
        try:
            self.lock.acquire() # matchgroups are not thread safe, but we need to be reentrant here
            if not self.matcher.matches(event):
                return "PASS"
            matchgroups = self.matcher.get_match_groups()
        finally:
            self.lock.release()
        
        self.set_aggregation_group_id(event,matchgroups)
        (group,lastmod) =  self.datasource.get_group_leader(event["group_id"])

        if group and time.time()-lastmod >= self.config["maxDelay"]:
            logging.debug("Cleared group %s " % event["group_id"])
            self.datasource.deactivate_group(event["group_id"])
            group = None
        
        if group and self.clear_matcher.matches(event):
            group_id = event["group_id"]
            event["group_id"] = None
            event["group_leader"] = None
            self.datasource.deactivate_group(group_id)
            group = None
            return "CLEAR"

            
        if group: 
            event["group_leader"] = group
            event["group_active"] = True
            return "AGGR"
        else:
            msg = self.create_aggregation_message(event,matchgroups)
            event["group_leader"] = -1
            event["alternative_message"] = msg
            event["group_active"] = True
            return "NEW"
        
        
    def hash(self,string):
        if USE_DEPRECATED_MD5:
            h = md5()
        else:
            h = md5.new()
        h.update(string)
        return h.digest()
    
    
    def create_matcher(self):
        self.matcher = None
        if "matcher" in self.config:
            self.matcher = matcher.Matcher(self.config["matcher"])
        
        self.use_fields_for_id = []
        if "matcherfield" in self.config:
            if not self.matcher:
                self.matcher = matcher.TrueMatcher()
            self.use_fields_for_id = self.config["matcherfield"].split(",")
        
        if "clear" in self.config:
            self.clear_matcher = matcher.Matcher(self.config["clear"])
        else:
            self.clear_matcher = matcher.FalseMatcher()
        
 
    
    def create_aggregation_message(self,event,matchgroups):
        msg = self.config["aggregateMessage"]
        tokens = re.findall("#\w+",msg)
        for token in tokens:
            if token[0] == '#':
                msg = msg.replace(token,event[token[1:]])
                continue
            if token[0] == '$':
                msg = msg.replace(token,matchgroups[token[1:]])
                continue
        return msg
        
        
    def set_aggregation_group_id(self,event,matchgroups):
        id = str(self.id)
        for field in self.use_fields_for_id:
            field = field.strip()
            id = id + str(event[field])
            
        attributes = matchgroups
        for i in attributes:
            id = id + i + attributes[i]
        event["group_id"] = self.hash(id)
        
        
        