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

from event import matcher

DB_TYPE_AGGREGATION_GROUP = 1


class AggregationProcessor(object):
    
    
    def setup(self,id,config = {}):
        self.id = id
        self.config = {
            "maxdelay": 3600*24,         # DEFAULT: Break aggregation when 
                                         # 10 minutes have passed without matching event
            "maxCount": -1,              # DEFAULT: No limit in how many events can be aggregated
            "datasource": None,
            "aggregatemessage": "GROUP: #message ($_COUNT events)"
        }
        
        for i in config:
            self.config[i] = config[i]
        logging.debug("Config for id %s -> %s" % (id,self.config))
        self.validate()
        self.lock = threading.Lock()
        self.datasource = self.config["datasource"]

        if "acknowledge_on_clear" in self.config:
            self.auto_acknowledge = True
        else:
            self.auto_acknowledge = False

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


        if self.autoclear:
            event["group_autoclear"] = 1

        self.set_aggregation_group_id(event,matchgroups)
        (group,lastmod) =  self.datasource.get_group_leader(event["group_id"])

        if group and time.time()-lastmod >= self.config["maxdelay"]:
            logging.debug("Cleared group %s " % event["group_id"])
            self.datasource.deactivate_group(event["group_id"])
            group = None

        if self.clear_matcher.matches(event):
            group_id = event["group_id"]
            event["clear_group_leader"] = group
            event["clear_group_id"] = group_id
            event["group_id"] = None
            self.datasource.deactivate_group(group_id)
            self.datasource.acknowledge_group(group_id,group)
            if self.auto_acknowledge:
                event["ack"] = 1
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
        else:
            self.matcher = matcher.TrueMatcher()
        
        self.use_fields_for_id = []
        if "matcherfield" in self.config:
            self.use_fields_for_id = self.config["matcherfield"].split(",")
        
        if "clear" in self.config:
            self.clear_matcher = matcher.Matcher(self.config["clear"])
            self.autoclear = self.auto_acknowledge
        else:
            self.clear_matcher = matcher.FalseMatcher()
            self.autoclear = False
        
 
    
    def create_aggregation_message(self,event,matchgroups):
        msg = self.config["aggregatemessage"]
        tokens = re.findall("[$#]\w+",msg)
        for token in tokens:
            if token[0] == '#':
                msg = msg.replace(token,str(event[token[1:]]))
                continue
            if token[0] == '$' and token[1:] in matchgroups:     
                msg = msg.replace(token,str(matchgroups[token[1:]]))
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
        
        
        
