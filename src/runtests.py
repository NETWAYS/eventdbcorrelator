#!/usr/bin/python
# To change this template, choose Tools | Templates
# and open the template in the editor.
from tests import *

import unittest
import logging

def suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(FilterTestCase))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(PipeReceptorTestCase))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(RSyslogTransformerTestCase))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(IPAddressTestCase))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(MatcherTestCase))
    return suite

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    runner = unittest.TextTestRunner()
    runner.run(suite())
    
    
