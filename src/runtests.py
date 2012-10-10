#!/usr/bin/python

from tests import *
from tests.integration import *
import unittest
import logging

def suite():
    suite = unittest.TestSuite()
    
    # Unit tests
#    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(PipeReceptorTestCase))
#    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(RSyslogTransformerTestCase))
#    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(IPAddressTestCase))
#    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(MatcherTestCase))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(MysqlDatasourceTest))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(SpoolDatasourceTest))
#    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(ChainTestCase))
#    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(AggregatorTestCase))
    
    # Integration tests
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(AggregatorMysqlTest))
    return suite

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    runner = unittest.TextTestRunner()
    runner.run(suite())
    
    
