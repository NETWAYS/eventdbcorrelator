# Helper class to transform strings, arrays, etc to EVent objects
import re
import logging
import os
import time
from event import Event

class SplitTransformer(object):

    def setup(self, id, config):
        self.id = id
        
        if "defaultmessage" in config:
            self.defaultMessage = config["defaultMessage"]
        else:
            self.defaultMessage = "No message given"
        self.fixed = {}
        
        if "fixed" in config:
            fixed = config["fixed"].split(", ")
            for keyval in fixed:
                keyval = keyval.split("=")
                self.fixed[keyval[0].lower()] = keyval[1]
        
        if "dateformat" in config:
            self.dateFormat = config["dateformat"]
        else:
            self.dateFormat = "%b %d %H:%M:%S"

        if "delimiter" in config:
            self.delimiter = config["delimiter"]
        else:
            self.delimiter = "\t"
        self.group_order = config["group_order"].split(" ")
        self.nr_of_groups = len(self.group_order)

    
    def set_current_year(self, st):
        now = time.localtime()
        return (now[0], st[1], st[2], st[3], st[4], st[5], st[6], st[7], st[8])
 
    def transform(self, string):
        try:
            dict = {} 

            stringtokens = re.split(self.delimiter, string)
            nr_of_tokens = len(stringtokens)
            tokenrange = range(0, nr_of_tokens)

            if nr_of_tokens != self.nr_of_groups:
                logging.warn("Event has %i properties, expected %i (raw event : %s)" %(nr_of_tokens, self.nr_of_groups, string))
                if self.nr_of_groups < nr_of_tokens:
                    tokenrange = range(0, self.nr_of_groups) # prevent overflow

            for pos in tokenrange:
                dict[self.group_order[pos]] = stringtokens[pos]

            return self.dict_to_event(dict)
        except Exception, e:
            logging.error("Couldn't transform %s to an event : %s" % (string, e))
            return None
 
    def dict_to_event(self, matchdict = {}):
        for i in self.fixed:
            matchdict[i] = self.fixed[i]
        if not "DATE" in matchdict:
            matchdict["DATE"] = time.ctime()
        else:
            if "TIME" in matchdict:
                matchdict["DATE"] = matchdict["DATE"]+" "+matchdict["TIME"]
            matchdict["DATE"] = time.strptime(matchdict["DATE"], self.dateFormat)
            if matchdict["DATE"][0] < 2000:
                matchdict["DATE"] = self.set_current_year(matchdict["DATE"])
            matchdict["DATE"] = time.mktime(matchdict["DATE"])
    
        if not "MESSAGE" in matchdict:
            matchdict["MESSAGE"] = self.defaultMessage
        
        event = Event(matchdict["MESSAGE"], matchdict["DATE"], matchdict)
        return event
    
    
