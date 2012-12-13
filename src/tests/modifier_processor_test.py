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
from processors import ModifierProcessor
import time

class MockDataSource(object):
    """ Mock datasource that provides faked flush and group handling

    """


    def __init__(self):
        self.count = 0
        self.table = "test"
        self.groups = {}
        self.flushed = []

    def get_group_leader(self, group_id):
        """ Returns the group leader from the internal groups dict

        """
        if group_id in self.groups:
            return (self.groups[group_id], time.time())
        return (None, time.time())
    
    def execute_after_flush(self, query, args = ()):
        """ Appends the query to this mocks flushed list to simulate flushes
            and be able to see what would have been flushed in practice
        """

        self.flushed.append(query)
        
    def reset(self):
        """ Resets the internal flushed list
        """

        self.flushed = []
        
class ModifierProcessorTest(unittest.TestCase):
    """ Tests modifiers, which are able to modify events or event groups on the fly
    """

    def test_event_overwrite(self):
        """ Test modification of single events

        """
        event = {
            "ack" : 0,
            "test" : 1,
            "test2" : "string"
        }
        
        processor = ModifierProcessor()
        processor.setup("test",{
            "overwrite" : "test=4;test2=test",
            "target" : "event"
        })
        
        assert processor.process(event) == "OK"
        assert event["test"] == '4'
        assert event["test2"] == "test"
        assert event["ack"] == 0
        
        processor.setup("test",{
            "overwrite" : "test=4;test2=test",
            "target" : "event",
            "acknowledge" : "True"
        })
        assert processor.process(event) == "OK"
        assert event["ack"] == 1

        
    def test_group_overwrite(self):
        """ Test modification of whole groups

        """
        ds = MockDataSource()
        event = {
            "ack" : 0,
            "test" : 1,
            "test2" : "string",
            "group_id" : 'test',
            "group_leader" : '12345'
            
        }
        
        processor = ModifierProcessor()
        processor.setup("test",{
            "overwrite" : "test=4;test2=test",
            "target" : "group"
        })
        
        assert processor.process(event) == "PASS" # No datasource
        ds.reset()
        processor.setup("test",{
            "overwrite" : "test=4;test2=test",
            "target" : "group",
            "datasource" : ds
        })
        
        assert processor.process(event) == "OK"
        assert len(ds.flushed) == 1
        
