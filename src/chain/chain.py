import logging
import re
import threading
import Queue
from event import matcher

# Time to block the thread until data is received. Higher values mean less
# System load,  lower values speed up program cancellation (as the thread is 
# only stopped after each read/timeout
QUEUE_WAIT_TIMEOUT=1

AFTER_DIRECTIVE='after'
NOT_AFTER_DIRECTIVE='not_after'


class Chain(threading.Thread):
    
    def setup(self, id,  config):
        self.event_chain = []
        self.id =  id
        
        
        if not "matcher" in config or config["matcher"] == "all":
            self.matcher = matcher.TrueMatcher()
        else:
            self.matcher = matcher.Matcher(config["matcher"])
        self.config = config
        '''
        Chains that will be called depending on the match result of this chain
        '''
        self.on_match_chains = []
        self.on_not_match_chains = []


        
    
    def setup_event_path(self):
        
        try:
            self.setup_dependencies()
            '''
            Only setup input for independent chains,  as otherwise the input from
            the previous chain is only forwarded to this chain
            '''
            if self.isIndependent:
                self.setup_input()
            
            self.setup_processors()
            self.ready = True
            
        except Exception,  e:
            logging.error("Chain %s could not be setup: %s." % (self.id,  e))
            self.ready = False


            
    '''
    Fetches the receptor from the instance list and registers this chains input
    buffer
    '''
    def setup_input(self):
        if not "in" in self.config:
            logging.warn(("Chain '%s' has no input defined and is independent. You should add an in: ... directive " % self.id) +
                            "to the config. This chain will be ignored." )
            return
        self.input = self.config["in"]
        if not self.input:
            raise Exception("Input %s does not exist" % self.config["in"])
        
        self.inQueue = Queue.Queue()
        self.input.register_queue(self.inQueue)


    
    def setup_dependencies(self):
        self.isIndependent = True
        for i in self.config:
            if i != AFTER_DIRECTIVE and i != NOT_AFTER_DIRECTIVE:
                continue
            self.isIndependent = False
            dependentChain = self.config[i]
            if not dependentChain:
                raise Exception("chain dependency %s:%s can't be resolved in chain %s " % (i, self.config[i], self.id))
            if i == AFTER_DIRECTIVE:
                dependentChain.register_chain_on_match(self)
            if i == NOT_AFTER_DIRECTIVE:
                dependentChain.register_chain_on_not_match(self)


            
    def setup_processors(self):
        for i in self.config:
            if i[0:2] == "to":
                self.register_processor(i, self.config[i])
        # sort by position,  so the chain elements can be run sequentially 
        self.event_chain.sort(lambda x,  y: x["pos"]-y["pos"])
        


    def register_processor(self, type, target):
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
        logging.debug("Event chain for %s : %s" %(self.id, self.event_chain))


    
    def get_condition_object(self, condition, basePos):
        condition_pos = re.match("(?P<COND_POS>\d+)\[(?P<COND_RETURN>\w+)\]", condition)
        if not condition_pos:
            raise Exception("Error in chain condition: %s couldn't be parsed (format is NR[CONDITION]" % condition)
        cdict = condition_pos.groupdict()
        if int(cdict["COND_POS"]) >= basePos:
            raise Exception("Logic error in chain %s: condition %s tests for future events", self.id, condition)

        return {
            "pos":    int(cdict["COND_POS"]),  
            "value":  cdict["COND_RETURN"]
        }
        
    
    def start(self):
        if not self.ready == True:
            logging.warn("Chain %s won't accept events due to setup errors..." % self.id)
            return
        if not self.isIndependent:
            logging.debug("Chain is not independent,  won't run in seperate thread" % self.id)
            return
        
        if "noThread" in self.config: # this is only for testing
            return self.run()
        return super(Chain, self).start()
    
    
    def run(self):
        try :
            self.running = True
            try :                
                self._wait_for_events()
            except OSError,  e:
                logging.warn("Error %s",  e)
            self.running = False

        finally:
            logging.debug("Finished Chain %s",  self.id)
        
        
    def _wait_for_events(self):
        while self.running:
            try:
                ev = self.inQueue.get(True, QUEUE_WAIT_TIMEOUT)
                self.on_event_recv(ev)
            except Queue.Empty,  e:
                pass
        
    def on_event_recv(self, ev):
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
        returnValues = {}
        for processor_obj in self.event_chain:
            matches = True
            for condition in processor_obj["conditions"]:
                dependent_pos = condition["pos"]
                if not dependent_pos in returnValues:
                    matches = False
                    break
                if returnValues[dependent_pos].lower() != condition["value"]:
                    matches = False
                    break
            if not matches:
                continue
            
            value = processor_obj["target"].process(ev)
            returnValues[processor_obj["pos"]] = value
        
    def stop(self):
        try:
            self.input.unregister_queue(self.inQueue)
            logging.debug("Stopping Chain %s " % self.id )
        finally:
            self.running = False        
            
    def register_chain_on_match(self, chain):
        self.on_match_chains.append(chain)
        pass
    
    def register_chain_on_not_match(self, chain):
        self.on_not_match_chains.append(chain)
        pass
