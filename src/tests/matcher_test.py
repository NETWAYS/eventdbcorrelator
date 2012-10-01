# To change this template, choose Tools | Templates
# and open the template in the editor.

import unittest
from event import *


class MatcherTestCase(unittest.TestCase):
    def testSimpleMessageMatch(self):
        curMatcher = Matcher("message is 'i am a testmessage'")
        testEvent = Event("I AM A Testmessage")
        assert curMatcher.matches(testEvent) == True

