#!/usr/bin/python

from tests import *

import unittest
import logging

def suite():
    suite = unittest.TestSuite()
    '''
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(PipeReceptorTestCase))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(RSyslogTransformerTestCase))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(IPAddressTestCase))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(MatcherTestCase))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(MysqlDatasourceTest))'''
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(ChainTestCase))
    return suite

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    runner = unittest.TextTestRunner()
    runner.run(suite())
    
    
