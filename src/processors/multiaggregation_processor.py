import os
from ConfigParser import ConfigParser
from processors import AggregationProcessor 
import logging 

CONFIG_DIRECTIVES = ("clear", "matcher", "aggregatemessage")

class MultiaggregationProcessor(object):
    
    def setup(self, id, config = {}):
        self.id = id
        self.config = {
            "maxdelay": 3600*24,         # DEFAULT: Break aggregation when 
                                         # 10 minutes have passed without matching event
            "maxCount": -1,              # DEFAULT: No limit in how many events can be aggregated
            "datasource": None,
            "acknowledge_on_clear": False
        }
        
        for i in config:
            self.config[i] = config[i]
        
        if not self.read_config_file():
            return None
        
        if not "aggregator_class" in self.config:
            self.config["aggregator_class"] = AggregationProcessor
        
        self.aggregator_class = self.config["aggregator_class"]
        self.setup_child_aggregators()
        
        
    def read_config_file(self):
        if not "ruleset" in self.config:
            logging.error("No ruleset given in Multiaggregation processor %s, aborting processor setup", self.id)
            return False
        if not os.path.exists(self.config["ruleset"]):
            logging.error("Could not setup multiaggregation processor %s, rulefile %s not found", self.id, self.config["ruleset"])
            return False
        self.rulesetparser = ConfigParser()
        self.rulesetparser.readfp(open(self.config["ruleset"]))
        logging.debug("Multiaggregation parser %s: setting up %i rules" % (self.id, len(self.rulesetparser.sections())))
        return True
    

    def setup_child_aggregators(self):
        self.aggregators= []
        
        for section in self.rulesetparser.sections():
            items = self.rulesetparser.items(section)
            cfg = self.config
            for (cfg_item, value) in items:
                if not cfg_item in CONFIG_DIRECTIVES:
                    logging.warn("Ignoring config setting %s in rule file %s" % (cfg_item, self.config["ruleset"]))
                else:
                    cfg[cfg_item] = value
                
            aggregator = self.aggregator_class()
            aggregator.setup(self.id+"_"+section, cfg)

            self.aggregators.append(aggregator)
        
        logging.debug("Registered %i aggregators underneath %s " % (len(self.aggregators), self.id))
    
    def process(self, event):
        for aggregator in self.aggregators:
            result = aggregator.process(event)
            if result == "PASS":
                continue
            else:
                return result
        return "PASS"
                
