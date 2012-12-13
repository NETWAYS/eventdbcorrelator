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
import unittest
from processors import MultiaggregationProcessor

class MockAggregator(object):
    """ Aggregator mock that fakes processing and returns a predefined
        value on process()
    """


    def __init__(self):
        self.config = {}
        self.state = "PASS"

    def setup(self, _id, config=None):
        """ Setup mock
        """
        self.id = _id
        self.config = config
    
    def process(self, event):
        """ Returns the previously defined 'state' property
        """
        return self.state
    
CFG_FILE = "./tests/testrules.rules"

class MultiAggregatorTest(unittest.TestCase):
    """ Tests for multiaggregators, which provide a simple interface for
        defining a bunch of aggregator definition at once

    """


    def test_setup(self):
        """ Tests the creation of a multiaggregator
        """


        processor = MultiaggregationProcessor()
        processor.setup("test", {
            "ruleset" : CFG_FILE,
            "aggregator_class" : MockAggregator,
            "aggregate_on_clear" : True
        })
        
        self.assertEqual(len(processor.aggregators), 2)
        ctr = 0
        for aggregator in processor.aggregators:
            ctr += 1
            self.assertTrue("aggregate_on_clear" in aggregator.config)
            self.assertEqual(aggregator.id,"test_aggr%i" % ctr)
            
    
    def test_all_pass(self):
        """ tests what happens if no filter should match

        """
        processor = MultiaggregationProcessor()
        processor.setup("test", {
            "ruleset" : CFG_FILE,
            "aggregator_class" : MockAggregator,
            "aggregate_on_clear" : True
        })
        
        # All processors pass here (as the mock defines it)
        self.assertEqual(processor.process("test"), "PASS")

    def test_first_matches(self):
        """ Test what happens if the first matches (and the others should not be
            executed)
        """
        processor = MultiaggregationProcessor()
        processor.setup("test", {
            "ruleset" : CFG_FILE,
            "aggregator_class" : MockAggregator,
            "aggregate_on_clear" : True
        })
        
        processor.aggregators[0].state = "AGGR"
        self.assertEqual(processor.process("test"),"AGGR")
    
    def test_second_matches(self):
        """ Test what happens if the second aggregator matches ( and the others should not be
            executed)
        """
        processor = MultiaggregationProcessor()
        processor.setup("test", {
            "ruleset" : CFG_FILE,
            "aggregator_class" : MockAggregator,
            "aggregate_on_clear" : True
        })
        
        processor.aggregators[1].state = "AGGR"
        self.assertEqual(processor.process("test"), "AGGR")
