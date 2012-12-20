#!/usr/bin/python
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
   SplitTransformerTest,
   IPAddressTestCase,
   MatcherTestCase,
   MysqlDatasourceTest,
   SpoolDatasourceTest,
   ChainTestCase,
   AggregatorTestCase,
   MultiAggregatorTest,
   CommandProcessorTest,
   ModifierProcessorTest
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
    
    
