from api.check_command import CheckCommand
import unittest
import urllib

class CheckCommandTest(unittest.TestCase):

    def test_parsing_simple_keyvalue(self):
        command1 = CheckCommand("key1=value1&key2=value2")
        self.assertEquals("value1", command1["key1"])
        self.assertEquals("value2", command1["key2"])
        self.assertTrue(command1.valid)

    def test_parsing_quoted_keyvalue(self):
        command1 = CheckCommand("key1=value1&key2=%s" % urllib.quote("val&&=ue2"))
        self.assertEquals("value1", command1["key1"])
        self.assertEquals("val&&=ue2", command1["key2"])
        self.assertTrue(command1.valid)

    def test_recognize_border_cases(self):
        command1 = CheckCommand("key1=value1&key2=&key3=test")
        self.assertEquals("value1", command1["key1"])
        self.assertEquals(None, command1["key2"]) # no error, but also no value
        self.assertEquals("test", command1["key3"])
        self.assertTrue(command1.valid)

    def test_handle_failing_patterns(self):
        command1 = CheckCommand("key1")
        self.assertFalse(command1.valid)
        command2 = CheckCommand("key1=test&&")
        self.assertFalse(command2.valid)
        command3 = CheckCommand("key1=te=st&&")
        self.assertFalse(command3.valid)

    def test_access_non_existing_properties(self):
        command1 = CheckCommand("key1=value1&key2=value2")
        self.assertEquals("value1", command1["key1"])
        self.assertEquals(None, command1["key3"])

    def test_host_is_uppercase(self):
        command = CheckCommand("host=imlowercase")
        self.assertEquals("IMLOWERCASE",command["host"])
        command = CheckCommand("host=")
        self.assertEquals(None,command["host"])

    def test_facility_parsing(self):
        command = CheckCommand("facility=1")
        self.assertEquals([1], command["facility"])
        command = CheckCommand("facility=1,,2,3,4")
        self.assertEquals(None, command["facility"])
        command = CheckCommand("facility=1,b,2,3,4")
        self.assertEquals(None, command["facility"])

    def test_priority_parsing(self):
        command = CheckCommand("priority=1")
        self.assertEquals([1], command["priority"])
        command = CheckCommand("priority=1,2,3,4,5")
        self.assertEquals([1,2,3,4,5], command["priority"])
        command = CheckCommand("priority=1,,2,3,4")
        self.assertEquals(None, command["priority"])
        command = CheckCommand("priority=1,b,2,3,4")
        self.assertEquals(None, command["priority"])

    def test_maxage_parsing(self):
        command = CheckCommand("maxage=")
        self.assertEquals(None,command["maxage"])
        command = CheckCommand("maxage=4")
        self.assertEquals(4,command["maxage"])

    def test_message_parsing(self):
        command = CheckCommand("message=message123")
        self.assertEquals("message123",command["message"])
        command = CheckCommand("message=")
        self.assertEquals(None,command["message123"])

    def test_start_timestamp_parsing(self):
        command = CheckCommand("start_timestamp=1234")
        self.assertEquals(1234, command["start_timestamp"])
        command = CheckCommand("start_timestamp=somethingelse")
        self.assertEquals(None, command["start_timestamp"])

    def test_program_parsing(self):
        command = CheckCommand("program=mail,mysql")
        self.assertEquals(["mail", "mysql"], command["program"])
        command = CheckCommand("program=")
        self.assertEquals(None, command["program"])

    def test_logtype_parsing(self):
        command = CheckCommand("logtype=1,2,3")
        self.assertEquals([1,2,3],command["logtype"])

    def test_prio_warning_parsing(self):
        command = CheckCommand("prio_warning=1,2,3,6&prio_critical=4,5,6")
        self.assertEquals([1,2,3,6], command["prio_warning"])
        self.assertEquals([4,5,6], command["prio_critical"])

    def test_ack_parsing(self):
        command = CheckCommand("ack=1")
        self.assertEquals(1, command["ack"])
        command = CheckCommand("ack=fuchs")
        self.assertEquals(None, command["ack"])