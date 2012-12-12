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
import logging
import re
import threading
import Queue
from event import matcher

# Time to block the thread until data is received. Higher values mean less
# System load, lower values speed up program cancellation (as the thread is 
# only stopped after each read/timeout
QUEUE_WAIT_TIMEOUT = 1

AFTER_DIRECTIVE = 'after'
NOT_AFTER_DIRECTIVE = 'not_after'

class Chain(threading.Thread):
    """ Chains connect processors and control their execution, depending on the return
        type, etc.

    """

    def setup(self, _id, config):
        """ Setup function as called by the InstanceFactory after the config is read 

        """
        self.event_chain = []
        self.id =  _id
        
        if not "matcher" in config or config["matcher"] == "all":
            self.matcher = matcher.TrueMatcher()
        else:
            self.matcher = matcher.Matcher(config["matcher"])
        self.config = config
        """
        Chains that will be called depending on the match result of this chain
        """
        self.on_match_chains = []
        self.on_not_match_chains = []

     
    def setup_event_path(self):
        """ Detects dependencies and sets up the event path for this chain

        """    
        try:
            self.setup_dependencies()
            """
            Only setup input for independent chains, as otherwise the input from
            the previous chain is only forwarded to this chain
            """
            if self.is_independent:
                self.setup_input()
            
            self.setup_processors()
            self.ready = True
            
        except Exception, e:
            logging.error("Chain %s could not be setup: %s." % (self.id, e))
            self.ready = False
 
    def setup_input(self):
        """
        Fetches the receptor from the instance list and registers the chains input
        buffer as an Queue()
        """

        if not "in" in self.config:
            logging.warn(("Chain '%s' has no input defined and is independent. You should add an in: ... directive " % self.id) +
                            "to the config. This chain will be ignored." )
            return
        self.input = self.config["in"]
        if not self.input:
            raise Exception("Input %s does not exist" % self.config["in"])
        
        self.in_queue = Queue.Queue()
        self.input.register_queue(self.in_queue)
    
    def setup_dependencies(self):
        """ Checks if an after or not_after directive exists and registers this chain to dependent chains if necessary
            sets the is_independent flag to True or False accroding to whether an after or not_after directive exists
        """
        self.is_independent = True
        for i in self.config:
            if i != AFTER_DIRECTIVE and i != NOT_AFTER_DIRECTIVE:
                continue
            self.is_independent = False
            dependent_chain = self.config[i]
            if not dependent_chain:
                raise Exception("chain dependency %s:%s can't be resolved in chain %s " % (i, self.config[i], self.id))
            if i == AFTER_DIRECTIVE:
                dependent_chain.register_chain_on_match(self)
            if i == NOT_AFTER_DIRECTIVE:
                dependent_chain.register_chain_on_not_match(self)

    def setup_processors(self):
        """ Registers every processor in this chaun alon with it's id and sorts them by their position number
        
        """
        for i in self.config:
            if i[0:2] == "to":
                self.register_processor(i, self.config[i])
        # sort by position, so the chain elements can be run sequentially 
        self.event_chain.sort(lambda x, y: x["pos"]-y["pos"])
        
    def register_processor(self, type, target):
        """ Registers a new processor in this chain 

        """
        type = type.split("_")
        pos = int(type[-1])
        
        if not target:
            raise Exception("Chain target %s does not exist " % target)
        
        processor_obj = {
            "pos"        :  pos,
            "conditions" :   [],
            "target"     :   target
        }
        
        for condition in type[1:-1]:
            processor_obj["conditions"].append(self.get_condition_object(condition, pos))
        
        self.event_chain.append(processor_obj)
        logging.debug("Event chain for %s : %s", self.id, self.event_chain )

    def get_condition_object(self, condition, base_pos):
        """ Reads conditions from a processor definition and sets returns them as a {pos: INT, value: STRING } object

        """
        condition_pos = re.match("(?P<COND_POS>\d+)\[(?P<COND_RETURN>\w+)\]", condition)
        if not condition_pos:
            raise Exception("Error in chain condition: %s couldn't be parsed (format is NR[CONDITION]" % condition)
        cdict = condition_pos.groupdict()
        if int(cdict["COND_POS"]) >= base_pos:
            raise Exception("Logic error in chain %s: condition %s tests for future events", self.id, condition)

        return {
            "pos":    int(cdict["COND_POS"]), 
            "value":  cdict["COND_RETURN"]
        }
        
    
    def start(self):
        """ Starts accepting events on this chain in a new thread
        If noThread is set, no new thread will be created, this is for testing purposes only
        
        """
        if not self.ready == True:
            logging.warn("Chain %s won't accept events due to setup errors...", self.id)
            return
        if not self.is_independent:
            logging.debug("Chain is not independent, won't run in seperate thread", self.id)
            return
        
        if "noThread" in self.config: # this is only for testing
            return self.run()
        return super(Chain, self).start()
    
    
    def run(self):
        """ Thread entry point, only calls _wait_for_events()

        """
        try :
            self.running = True
            try :                
                self._wait_for_events()
            except OSError, e:
                logging.warn("Error %s", e)
            self.running = False

        finally:
            logging.debug("Finished Chain %s", self.id)
        
    def _wait_for_events(self):
        """ Reads events from the in_queue and processes them according to the chain structure and conditinal settings

        """
        while self.running:
            try:
                ev = self.in_queue.get(True, QUEUE_WAIT_TIMEOUT)
                self.on_event_recv(ev)
            except Queue.Empty, e:
                pass
        
    def on_event_recv(self, ev):
        """ Called when an event is received. Tests if the general chain matcher applies and routes the event through the chain if so

        """
        if not self.matcher.matches(ev):
            logging.debug("not processing %s " % ev)
            if self.on_not_match_chains:
                for chain in self.on_not_match_chains:
                    chain.on_event_recv(ev)
            return
        self.process_event(ev)
        
        if self.on_match_chains:
            for chain in self.on_match_chains:
                chain.on_event_recv(ev)

    def process_event(self, ev):
        """ Runs every processor in the chain (except conditional processors that don't match)
            
        """
        return_values = {}
        for processor_obj in self.event_chain:
            matches = True
            for condition in processor_obj["conditions"]:
                dependent_pos = condition["pos"]
                if not dependent_pos in return_values:
                    matches = False
                    break
                if return_values[dependent_pos].lower() != condition["value"]:
                    matches = False
                    break
            if not matches:
                continue
            
            value = processor_obj["target"].process(ev)
            return_values[processor_obj["pos"]] = value
        
    def stop(self):
        """ Unregisters the input buffer from the receptor and sets running=false, causing the chain thread to terminate

        """
        try:
            self.input.unregister_queue(self.in_queue)
            logging.debug("Stopping Chain %s ", self.id )
        finally:
            self.running = False        
            
    def register_chain_on_match(self, chain):
        """ Registers a chain that will be called after the matcher of this chain matches an event
            
        """
        self.on_match_chains.append(chain)
    
    def register_chain_on_not_match(self, chain):
        """ Registers a new chain that will be called after the matcher of this chain does not match an event

        """
        self.on_not_match_chains.append(chain)
