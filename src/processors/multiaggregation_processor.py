"""
EDBC - Message correlation and aggregation engine for passive monitoring events
Copyright (C) 2012  NETWAYS GmbH

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""
import os
from ConfigParser import ConfigParser
from processors import AggregationProcessor 
import logging 

CONFIG_DIRECTIVES = ("clear","matcher","aggregatemessage","matcherfield")

class MultiaggregationProcessor(object):
    """ MultiaggregationProcessor act upon normal AggregationProcessors
        and allow to define multiple rules in one rules file. The processor
        then handles creation of the actual Aggregationprocessors, which
        makes configuration a lot easier.

    """

    def setup(self, id, config = {}):
        """ Setup method that configures the instance of this method

            InstanceFactory calls this with the id and configuration from datasource
            definitions defined in the conf.d directory
        """
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
        """ Loads the configuration file defined in the ruleset directive of this processors
            cfg definition
        """

        if not "ruleset" in self.config:
            logging.error("No ruleset given in Multiaggregation processor %s, aborting processor setup", self.id)
            return False
        if not os.path.exists(self.config["ruleset"]):
            logging.error("Could not setup multiaggregation processor %s, rulefile %s not found", self.id, self.config["ruleset"])
            return False

        self.rulesetparser = ConfigParser()
        self.rulesetparser.readfp(open(self.config["ruleset"]))
        logging.debug("Multiaggregation parser %s: setting up %i rules", self.id,len(self.rulesetparser.sections()))
        return True
    

    def setup_child_aggregators(self):
        """ Creates single aggregationprocessors as with the rules defined in the ruleset file

        """
        self.aggregators= []
        
        for section in self.rulesetparser.sections():
            items = self.rulesetparser.items(section)
            cfg = self.config
            for (cfg_item,value) in items:
                if not cfg_item in CONFIG_DIRECTIVES:
                    logging.warn("Ignoring config setting %s in rule file %s", cfg_item, self.config["ruleset"])
                else:
                    cfg[cfg_item] = value
                
            aggregator = self.aggregator_class()
            aggregator.setup(self.id + "_" + section,cfg)

            self.aggregators.append(aggregator)
        
        logging.debug("Registered %i aggregators underneath %s ", len(self.aggregators), self.id)
    
    def process(self,event):
        """ Routes the event through all aggregationprocessors, stopping at the first that doesn't return
            "PASS" and returns the status of the last processed AggregationProcessor

        """
        for aggregator in self.aggregators:
            result = aggregator.process(event)
            if result == "PASS":
                continue
            else:
                return result
        return "PASS"
                