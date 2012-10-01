# To change this template, choose Tools | Templates
# and open the template in the editor.

import unittest
from event.event import *
from datasource.filter import Filter, FilterGroup

class  FilterTestCase(unittest.TestCase):
    def setUp(self):
        self.testEvent1 = Event("pipe","this is a test message",{
            "severity": 5,
            "community": "public",
            "test": "value"
        })
        self.testEvent2 = Event("pipe","additional test message",{
            "severity": 1,
            "attribute" : 'value2',
            "community": "private",
            "test": "value2"
        })
        self.testEvent3 = Event("snmp","NOTIFY switch sw1242-sd down",{
            "severity": 9,
            "manufacturer" : 'linksys',
            "community": "public",
            "test": "value3"
        })
        
    def test_exact_filter(self):
        filter = Filter("message","IS","this is a test message");
        assert filter.matches(self.testEvent1) == True
        assert filter.matches(self.testEvent2) != True
        assert filter.matches(self.testEvent3) != True

    def test_regexp_filter(self):
        filter = Filter("message","MATCH","(a.*) (test message)");
        assert filter.matches(self.testEvent1) == True
        assert filter.matches(self.testEvent2) == True
        assert filter.matches(self.testEvent3) == False
        
    def test_relational_filter(self):
        filter = Filter("severity",">",2);
        assert filter.matches(self.testEvent1) == True
        assert filter.matches(self.testEvent2) == False
        assert filter.matches(self.testEvent3) == True
        
        filter = Filter("severity","<",2);
        assert filter.matches(self.testEvent1) != True
        assert filter.matches(self.testEvent2) != False
        assert filter.matches(self.testEvent3) != True
        
    def test_set_filter(self):
        filter = Filter("test","IN","value,value2")
        assert filter.matches(self.testEvent1) == True
        assert filter.matches(self.testEvent2) == True
        assert filter.matches(self.testEvent3) == False

    def test_filtergroup_simple(self):
        setFilter = Filter("test","IN","value,value2")
        regexpFilter = Filter("message","MATCH","(a.*) (test message)");
        severityFilter = Filter("severity",">",2);

        filtergroup = FilterGroup("AND")
        filtergroup.add([setFilter,regexpFilter])
        assert filtergroup.matches(self.testEvent1) == True
        assert filtergroup.matches(self.testEvent2) == True
        assert filtergroup.matches(self.testEvent3) == False
        
        filtergroup.add(severityFilter)
        assert filtergroup.matches(self.testEvent1) == True
        assert filtergroup.matches(self.testEvent2) == False
        assert filtergroup.matches(self.testEvent3) == False

    def test_filtergroup_nested(self):
        filtergroup1 = FilterGroup("AND")
        setFilter = Filter("test","IN","value,value2")
        severityFilter = Filter("severity",">",2);
        commFilter = Filter("community","=","public");
        
        regexpFilter = Filter("message","MATCH","(a.*) (test message)");        
        filtergroup1.add([setFilter,regexpFilter])
        
        filtergroup2 = FilterGroup("AND")
        filtergroup2.add([severityFilter,commFilter])
        
        filtergroup_base = FilterGroup("OR")
        filtergroup_base.add([filtergroup1,filtergroup2])
        
        assert filtergroup1.matches(self.testEvent1) == True
        assert filtergroup1.matches(self.testEvent2) == True
        assert filtergroup1.matches(self.testEvent3) == False
        
        assert filtergroup2.matches(self.testEvent1) == True
        assert filtergroup2.matches(self.testEvent2) == False
        assert filtergroup2.matches(self.testEvent3) == True
        
        assert filtergroup_base.matches(self.testEvent1) == True
        assert filtergroup_base.matches(self.testEvent2) == True
        assert filtergroup_base.matches(self.testEvent3) == True
        
    def test_to_sql(self):
        filtergroup1 = FilterGroup("AND")
        setFilter = Filter("test","IN","value,value2")
        severityFilter = Filter("severity",">",2);
        commFilter = Filter("community","=","public");
        
        regexpFilter = Filter("message","MATCH","(a.*) (test message)");        
        filtergroup1.add([setFilter,regexpFilter])
        
        filtergroup2 = FilterGroup("AND")
        filtergroup2.add([severityFilter,commFilter])
        
        filtergroup_base = FilterGroup("OR")
        filtergroup_base.add([filtergroup1,filtergroup2])
        
        
if __name__ == '__main__':
    unittest.main()

