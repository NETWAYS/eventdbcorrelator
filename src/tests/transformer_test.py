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

from network.ip_address import IPAddress
from event import SnmpTransformer, StringTransformer, SplitTransformer


class RSyslogTransformerTestCase(unittest.TestCase):
    """ Tests whether the RSysLog format ist working by testing a few messages

    """

    def setUp(self):
        """ Creates a few rsyslog messages like they occur on almost every workstation

        """
        self.FORMAT = r"^(?P<DATE>[a-zA-Z]{2,3} \d\d \d\d:\d\d:\d\d) (?P<HOST>[^ ]+)( (?P<PROGRAM>[^:]+):)? (?P<MESSAGE>.*)$"
        self.LOG_MESSAGES = "./tests/logtest.syslog"
        self.MAX_TIME_PER_EVENT = 0.001 # Hard limit on how long an incoming event should take on average
        self.rsyslog = [
            ("Sep 21 12:40:02 localhost syslogd 1.4.1: restart.", {
                #"CREATED" : 1348224002,
                "HOST" : "localhost",
                "PROGRAM" : "syslogd 1.4.1",
                "MESSAGE" : "restart."
            }),
            ("Sep 21 12:40:02 localhost kernel: klogd 1.4.1, log source = /proc/kmsg started.", {
                #"CREATED" : 1348224002,
                "HOST" : "localhost",
                "PROGRAM" : "kernel",
                "MESSAGE" : "klogd 1.4.1, log source = /proc/kmsg started."
            }),
            ("Sep 21 12:40:07 localhost icinga: The command defined for service SYS_LINUX_SWAP does not exist", {
                #"CREATED" : 1348224007,
                "HOST" : "localhost",
                "PROGRAM" : "icinga",
                "MESSAGE" : "The command defined for service SYS_LINUX_SWAP does not exist"
            }),
            ("Sep 27 10:08:45 ws-test kernel: [179599.999522] type=1701 audit(1348733325.650:64): auid=4294967295 uid=1000 gid=1000 ses=4294967295 pid=26544 comm=\"chrome\" reason=\"seccomp\" sig=0 syscall=39 compat=0 ip=0x7fd83f0bc6d9 code=0x50001", {
                #"CREATED" : 1348733325,
                "HOST" : "ws-test",
                "PROGRAM" : "kernel",
                "MESSAGE" : "[179599.999522] type=1701 audit(1348733325.650:64): auid=4294967295 uid=1000 gid=1000 ses=4294967295 pid=26544 comm=\"chrome\" reason=\"seccomp\" sig=0 syscall=39 compat=0 ip=0x7fd83f0bc6d9 code=0x50001"
            }),
        ]
        
    def test_rsyslog_transformer(self):
        """ Tests whether the messages result in the expected events after transformation

        """
        transformer = StringTransformer()
        transformer.setup("test", {
            "format" : self.FORMAT
        })
        for message_event_pair in self.rsyslog:
            event = transformer.transform(message_event_pair[0])
            for key in message_event_pair[1]:
                assert event != None
                assert event[key] == message_event_pair[1][key]
#
#    def test_rsyslog_performance(self):
#        transformer = StringTransformer()
#        transformer.setup("test",{
#            "format": self.FORMAT
#        })
#        logfile = open(self.LOG_MESSAGES,"r+")  
#        try:
#            linectr=0
#            start = time.time()
#            for line in logfile:
#                linectr += 1
#                ev = transformer.transform(line)
#                try:
#                    assert ev != None
#                except Exception, e:
#                    logging.debug("Line '%s' failed", line)
#                    raise e
#            required = time.time()-start
#            avg = required/linectr
#            assert required < self.MAX_TIME_PER_EVENT*linectr
#            
#        finally:
#            logfile.close()
    
class SNMPTransformerTest(unittest.TestCase):
    """ SNMPTransformers contain more logic than normal transformers, as they read
        snmpttconvertmib generated files

    """
    def test_setup(self):
        """ Tests the setup of the snmp transformer

        """

        transformer = SnmpTransformer()
        transformer.setup("test",{
            "mib_dir" : "/tmp/"
        })
      
    def test_mib_parsing(self):
        """ Tests whether simple mib files are correctly parsed and variables are substituted

        """
        transformer = SnmpTransformer()
        transformer.setup("test",{
            "mib_dir" : "/dev/null"
        })
        # Example from
        mibs = transformer.parse_file({
            "EVENT test_event 0.1.4.* \"test category\" severity" : 0,
            "FORMAT test format  $* $_ #": 1,
            "REGEX (Building alarm 3)(Computer room high temperature)": 2,
            "REGEX (Building alarm 4)(Moisture detection alarm)" : 3,
            "REGEX (roOm)(ROOM)ig" : 4,
            "REGEX (UPS)(The big UPS)" : 5,
            "REGEX (\s+)( )g" : 6,
            "REGEX (tes(t))$" : 7  #invalid line
        })
        assert(len(mibs) == 1)
        mib = mibs[0]
        transformer.registered_mibs.append(mib)
        assert mib["event_name"] == "test_event"
        assert mib["oid"] == "0.1.4.*"
        assert mib["category"] == "test category"
        assert mib["severity"] == "severity"
        assert mib["format"] == "test format  $* $_ #"

        # Check correct regexp parsing
        assert "regexp" in mib
        assert len(mib["regexp"]) == 5
        assert transformer.get_mib_for("0.1.4.5.6.7") != None
        assert transformer.get_mib_for("0.1.4.5.6.7") == mib

    def test_multiple_traps_in_one_file(self):

        transformer = SnmpTransformer()
        transformer.setup("test",{
            "mib_dir" : "/dev/null"
        })
        # Example from
        mibs = transformer.parse_file({
            "EVENT test_event 0.1.4.* \"test category\" severity" : 0,
            "FORMAT test format  $* $_ #": 1,
            "EVENT test_event 0.1.5.* \"test category2\" severity" : 2,
            "FORMAT test format  $* $_ #": 3,
            "EVENT test_event 0.1.6.* \"test category2\" severity" : 4,
            "FORMAT test format  $* $_ #": 5
        })


        assert(len(mibs) == 3)



    def test_transform_simple(self):
        """ Simple (non substituted) message transformation

        """
        transformer = SnmpTransformer()
        transformer.setup("test",{
            "mib_dir" : "/dev/null"
        })
        transformer.registered_mibs += (transformer.parse_file({
            "EVENT test_event .1.3.6.1.4.1.2021.13.990.0.17 \"test category\" severity" : 0,
            "FORMAT $*" : 1
        }))
        str = 'HOST:testhost.localdomain;IP:UDP: [127.0.5.1]:50935;VARS:.1.3.6.1.2.1.1.3.0 = 2:22:16:27.46 ; .1.3.6.1.6.3.1.1.4.1.0 = .1.3.6.1.4.1.2021.13.990.0.17 ; .1.3.6.1.2.1.1.6.0 = Argument 1 ; .1.3.6.1.6.3.18.1.3.0 = 127.0.0.1 ; .1.3.6.1.6.3.18.1.4.0 = "public" ; .1.3.6.1.6.3.1.1.4.3.0 = .1.3.6.1.4.1.2021.13.990'
        event = transformer.transform(str)
        import logging
        from pprint import pprint

        assert event["host_address"] == "127.0.5.1"
        assert event["host_name"] == "testhost.localdomain"

        assert event["message"] == "Argument 1"

    def test_regexp_execution_1(self):
        """ First example of http://snmptt.sourceforge.net/docs/snmptt.shtml#SNMPTT.CONF-REGEX

        """
        transformer = SnmpTransformer()
        transformer.setup("test",{
            "mib_dir" : "/dev/null"
        })
        transformer.registered_mibs += (transformer.parse_file({
            "EVENT test_event .1.3.6.1.4.1.2021.13.990.0.17 \"test category\" severity" : 0,
            "FORMAT $*" : 1,
            r"REGEX (Building alarm 3)(Computer room high temperature)": 2,
            r"REGEX (Building alarm 4)(Moisture detection alarm)" : 3,
            r"REGEX (roOm)(ROOM)ig" : 4,
            r"REGEX (UPS)(The big UPS)" : 5,
            r"REGEX (\s+)( )g" : 6,
        }))
        str = 'HOST:testhost.localdomain;IP:UDP: [127.0.5.1]:50935;VARS:.1.3.6.1.2.1.1.3.0 = 2:22:16:27.46 ; .1.3.6.1.6.3.1.1.4.1.0 = .1.3.6.1.4.1.2021.13.990.0.17 ; .1.3.6.1.2.1.1.6.0 = UPS has       detected a      building alarm.       Cause: UPS1 Alarm #14: Building alarm 3 ; .1.3.6.1.6.3.18.1.3.0 = 127.0.0.1 ; .1.3.6.1.6.3.18.1.4.0 = "public" ; .1.3.6.1.6.3.1.1.4.3.0 = .1.3.6.1.4.1.2021.13.990'
        event = transformer.transform(str)

        assert event["host_address"] == "127.0.5.1"
        assert event["host_name"] == "testhost.localdomain"
        assert event["message"] == "The big UPS has detected a building alarm. Cause: UPS1 Alarm #14: Computer ROOM high temperature"

    def test_strip_domain(self):
        """ First example of http://snmptt.sourceforge.net/docs/snmptt.shtml#SNMPTT.CONF-REGEX

        """
        transformer = SnmpTransformer()
        transformer.setup("test",{
            "mib_dir" : "/dev/null",
            "strip_domain": 'localdomain.int'
        })
        transformer.registered_mibs += (transformer.parse_file({
            "EVENT test_event .1.3.6.1.4.1.2021.13.990.0.17 \"test category\" severity" : 0,
            "FORMAT $*" : 1,
            r"REGEX (Building alarm 3)(Computer room high temperature)": 2,
            r"REGEX (Building alarm 4)(Moisture detection alarm)" : 3,
            r"REGEX (roOm)(ROOM)ig" : 4,
            r"REGEX (UPS)(The big UPS)" : 5,
            r"REGEX (\s+)( )g" : 6,
            }))
        str = 'HOST:testhost.localdomain.int;IP:UDP: [127.0.5.1]:50935;VARS:.1.3.6.1.2.1.1.3.0 = 2:22:16:27.46 ; .1.3.6.1.6.3.1.1.4.1.0 = .1.3.6.1.4.1.2021.13.990.0.17 ; .1.3.6.1.2.1.1.6.0 = UPS has       detected a      building alarm.       Cause: UPS1 Alarm #14: Building alarm 3 ; .1.3.6.1.6.3.18.1.3.0 = 127.0.0.1 ; .1.3.6.1.6.3.18.1.4.0 = "public" ; .1.3.6.1.6.3.1.1.4.3.0 = .1.3.6.1.4.1.2021.13.990'
        event = transformer.transform(str)

        assert event["host_address"] == "127.0.5.1"

        assert event["host_name"] == "testhost"
        assert event["message"] == "The big UPS has detected a building alarm. Cause: UPS1 Alarm #14: Computer ROOM high temperature"


    def test_regexp_execution_2(self):
        """ Second example of http://snmptt.sourceforge.net/docs/snmptt.shtml#SNMPTT.CONF-REGEX

        """
        transformer = SnmpTransformer()
        transformer.setup("test",{
            "mib_dir" : "/dev/null"
        })
        transformer.registered_mibs += (transformer.parse_file({
            "EVENT test_event .1.3.6.1.4.1.2021.13.990.0.17 \"test category\" severity" : 0,
            "FORMAT $*" : 1,
            r"REGEX (\(1\))(One)" : 2,
            r"REGEX (\(2\))((Two))": 3
        }))
        str = 'HOST:testhost.localdomain;IP:UDP: [127.0.5.1]:50935;VARS:.1.3.6.1.2.1.1.3.0 = 2:22:16:27.46 ; .1.3.6.1.6.3.1.1.4.1.0 = .1.3.6.1.4.1.2021.13.990.0.17 ; .1.3.6.1.2.1.1.6.0 = Alarm (1) and (2) has been triggered ; .1.3.6.1.6.3.18.1.3.0 = 127.0.0.1 ; .1.3.6.1.6.3.18.1.4.0 = "public" ; .1.3.6.1.6.3.1.1.4.3.0 = .1.3.6.1.4.1.2021.13.990'
        event = transformer.transform(str)

        assert event["host_address"] == "127.0.5.1"
        assert event["host_name"] == "testhost.localdomain"
        assert event["message"] == "Alarm One and (Two) has been triggered"

    def test_regexp_execution_groups(self):
        """ Second example of http://snmptt.sourceforge.net/docs/snmptt.shtml#SNMPTT.CONF-REGEX

        """
        transformer = SnmpTransformer()
        transformer.setup("test",{
            "mib_dir" : "/dev/null"
        })
        transformer.registered_mibs += (transformer.parse_file({
            "EVENT test_event .1.3.6.1.4.1.2021.13.990.0.17 \"test category\" severity" : 0,
            "FORMAT $*" : 1,
            r"REGEX (The system has logged exception error (\d+) for the service (\w+))(Service \2 generated error \1)" : 2
        }))
        str = 'HOST:testhost.localdomain;IP:UDP: [192.168.2.15]:42992->[192.168.2.15];VARS:.1.3.6.1.2.1.1.3.0 = 2:22:16:27.46 ; .1.3.6.1.6.3.1.1.4.1.0 = .1.3.6.1.4.1.2021.13.990.0.17 ; .1.3.6.1.2.1.1.6.0 = The system has logged exception error 55 for the service testservice ; .1.3.6.1.6.3.18.1.3.0 = 127.0.0.1 ; .1.3.6.1.6.3.18.1.4.0 = "public" ; .1.3.6.1.6.3.1.1.4.3.0 = .1.3.6.1.4.1.2021.13.990'
        event = transformer.transform(str)

        assert event["host_address"] == "192.168.2.15"
        assert event["host_name"] == "testhost.localdomain"
        assert event["message"] == "Service testservice generated error 55"

class SplitTransformerTest(unittest.TestCase):
    """ Splittransformers just split the input by a specified character

    """

    def test_implicit_tabulator_split(self):
        """ Test the default setting, split by tab
        """
        transformer = SplitTransformer()
        transformer.setup("test", {
            "dateformat" : "%Y-%m-%d %H:%M:%S",
            "group_order" : "HOST_NAME HOST_ADDRESS PRIORITY FACILITY TIME DATE MESSAGE"  
        })
        teststring = "test_host\t42.2.53.52\t5\t4\t11:00:24\t2012-12-10\tTestmessage"
        event = transformer.transform(teststring)
        assert event != None
        assert event["host_name"] == "test_host"
        assert event["host_address"] == IPAddress("42.2.53.52")
        assert event["priority"] == "5"
        assert event["facility"] == "4"
        assert event["message"] == "Testmessage"
        

    def test_explicit_delimiter_specification(self):
        """ Test whether own delimiters are correctly recognized, also if they are multi character
            delimiters

        """
        transformer = SplitTransformer()
        transformer.setup("test", {
            "dateformat" : "%Y-%m-%d %H:%M:%S",
            "delimiter" : "\.-\.",
            "group_order" : "HOST_NAME HOST_ADDRESS PRIORITY FACILITY TIME DATE MESSAGE"  
        })
        teststring = "test_host.-.42.2.53.52.-.5.-.4.-.11:00:24.-.2012-12-10.-.Testmessage"
        event = transformer.transform(teststring)
        assert event != None
        assert event["host_name"] == "test_host"
        assert event["host_address"] == IPAddress("42.2.53.52")
        assert event["priority"] == "5"
        assert event["facility"] == "4"
        assert event["message"] == "Testmessage"
        
