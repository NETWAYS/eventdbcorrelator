#!/usr/bin/python

from tests import *
from tests.integration import *
import unittest
import logging

UNITTESTS = [
    InstanceFactoryTest,
    PipeReceptorTestCase,
    SNMPReceptorTest,
    SNMPTransformerTest,
    RSyslogTransformerTestCase,
    IPAddressTestCase,
    MatcherTestCase,
    MysqlDatasourceTest,
    SpoolDatasourceTest,
    ChainTestCase,
    AggregatorTestCase,
    CommandProcessorTest
]


def suite():
    suite = unittest.TestSuite()
    
    # Unit tests
    for utest in UNITTESTS:
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(utest))
    
    # Integration tests
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(AggregatorMysqlTest))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(MySQLDataSourceSpoolTest))
    return suite

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    runner = unittest.TextTestRunner()
    runner.run(suite())
    
    
