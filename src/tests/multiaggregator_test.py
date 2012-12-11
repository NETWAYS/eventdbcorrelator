import unittest
from processors import MultiaggregationProcessor
from event import Event
import time

class MockAggregator(object):
    def __init__(self):
        self.config = {}
        self.state = "PASS"
    
    def setup(self, id, config={}):
        self.id = id
        self.config = config
    
    def process(self, event):
        return self.state
    
CFG_FILE = "./tests/testrules.rules"

class MultiAggregatorTest(unittest.TestCase):
    
    def test_setup(self):
        processor = MultiaggregationProcessor()
        processor.setup("test", {
            "ruleset" : CFG_FILE,
            "aggregator_class" : MockAggregator,
            "aggregate_on_clear" : True
        })
        
        self.assertEqual(len(processor.aggregators), 2)
        ctr = 0
        for aggregator in processor.aggregators:
            ctr = ctr + 1
            self.assertTrue("aggregate_on_clear" in aggregator.config)
            self.assertEqual(aggregator.id, "test_aggr%i" % ctr)
            
    
    def test_all_pass(self):
        processor = MultiaggregationProcessor()
        processor.setup("test", {
            "ruleset" : CFG_FILE,
            "aggregator_class" : MockAggregator,
            "aggregate_on_clear" : True
        })
        
        # All processors pass here (as the mock defines it)
        self.assertEqual(processor.process("test"), "PASS")

    def test_first_matches(self):
        processor = MultiaggregationProcessor()
        processor.setup("test", {
            "ruleset" : CFG_FILE,
            "aggregator_class" : MockAggregator,
            "aggregate_on_clear" : True
        })
        
        processor.aggregators[0].state = "AGGR"
        self.assertEqual(processor.process("test"), "AGGR")
    
    def test_second_matches(self):
        processor = MultiaggregationProcessor()
        processor.setup("test", {
            "ruleset" : CFG_FILE,
            "aggregator_class" : MockAggregator,
            "aggregate_on_clear" : True
        })
        
        processor.aggregators[1].state = "AGGR"
        self.assertEqual(processor.process("test"), "AGGR")
