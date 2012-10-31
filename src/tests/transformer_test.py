# To change this template, choose Tools | Templates
# and open the template in the editor.
import unittest
import time
import logging
from event import IPAddress
from event import SnmpTransformer,StringTransformer


class RSyslogTransformerTestCase(unittest.TestCase):

    def setUp(self):
        self.FORMAT = "^(?P<DATE>[a-zA-Z]{2,3} \d\d \d\d:\d\d:\d\d) (?P<HOST>[^ ]+)( (?P<PROGRAM>[^:]+):)? (?P<MESSAGE>.*)$"
        self.LOG_MESSAGES = "./tests/logtest.syslog"
        self.MAX_TIME_PER_EVENT = 0.0001 # Hard limit on how long an incoming event should take on average
        self.rsyslog = [
            ("Sep 21 12:40:02 localhost syslogd 1.4.1: restart.",{
                "CREATED" : 1348224002,
                "HOST" : "localhost",
                "PROGRAM" : "syslogd 1.4.1",
                "MESSAGE" : "restart."
            }),
            ("Sep 21 12:40:02 localhost kernel: klogd 1.4.1, log source = /proc/kmsg started.",{
                "CREATED" : 1348224002,
                "HOST" : "localhost",
                "PROGRAM" : "kernel",
                "MESSAGE" : "klogd 1.4.1, log source = /proc/kmsg started."
            }),
            ("Sep 21 12:40:07 localhost icinga: The command defined for service SYS_LINUX_SWAP does not exist",{
                "CREATED" : 1348224007,
                "HOST" : "localhost",
                "PROGRAM" : "icinga",
                "MESSAGE" : "The command defined for service SYS_LINUX_SWAP does not exist"
            }),
            ("Sep 27 10:08:45 ws-test kernel: [179599.999522] type=1701 audit(1348733325.650:64): auid=4294967295 uid=1000 gid=1000 ses=4294967295 pid=26544 comm=\"chrome\" reason=\"seccomp\" sig=0 syscall=39 compat=0 ip=0x7fd83f0bc6d9 code=0x50001",{
                "CREATED" : 1348733325,
                "HOST" : "ws-test",
                "PROGRAM" : "kernel",
                "MESSAGE" : "[179599.999522] type=1701 audit(1348733325.650:64): auid=4294967295 uid=1000 gid=1000 ses=4294967295 pid=26544 comm=\"chrome\" reason=\"seccomp\" sig=0 syscall=39 compat=0 ip=0x7fd83f0bc6d9 code=0x50001"
            }),
        ]
        
    def test_rsyslog_transformer(self):
        transformer = StringTransformer()
        transformer.setup("test",{
            "format": self.FORMAT
        })
        for messageEventPair in self.rsyslog:
            event = transformer.transform(messageEventPair[0])
            for key in messageEventPair[1]:
                assert event != None
                assert event[key] == messageEventPair[1][key]

    def test_rsyslog_performance(self):
        transformer = StringTransformer()
        transformer.setup("test",{
            "format": self.FORMAT
        })
        logfile = open(self.LOG_MESSAGES,"r+")  
        try:
            linectr=0
            start = time.time()
            for line in logfile:
                linectr += 1
                ev = transformer.transform(line)
                try:
                    assert ev != None
                except Exception, e:
                    logging.debug("Line '%s' failed",line)
                    raise e
            required = time.time()-start
            avg = required/linectr
            assert required < self.MAX_TIME_PER_EVENT*linectr
            
        finally:
            logfile.close()
    
class SNMPTransformerTest(unittest.TestCase):
    
    def test_setup(self):
        transformer = SnmpTransformer()
        transformer.setup("test",{
            "mib_dir" : "/tmp/"
        })
      
    def test_mib_parsing(self):
        transformer = SnmpTransformer()
        transformer.setup("test",{
            "mib_dir" : "/dev/null"
        })
        mib = transformer.parse_file({
            "EVENT test_event 0.1.4.* \"test category\" severity" : 0,
            "FORMAT test format  $* $_ #": 1
        })
        transformer.registered_mibs.append(mib)
        assert mib["event_name"] == "test_event"
        assert mib["oid"] == "0.1.4.*"
        assert mib["category"] == "test category"
        assert mib["severity"] == "severity"
        assert mib["format"] == "test format  $* $_ #"
        assert transformer.get_mib_for("0.1.4.5.6.7") != None
        assert transformer.get_mib_for("0.1.4.5.6.7") == mib
        
        
    def test_transform_simple(self):
        transformer = SnmpTransformer()
        transformer.setup("test",{
            "mib_dir" : "/dev/null"
        })
        transformer.registered_mibs.append(transformer.parse_file({
            "EVENT test_event .1.3.6.1.4.1.2021.13.990.0.17 \"test category\" severity" : 0,
            "FORMAT $*" : 1
        }))
        str = 'HOST:testhost.localdomain;IP:UDP: [127.0.5.1]:50935;VARS:.1.3.6.1.2.1.1.3.0 = 2:22:16:27.46 ; .1.3.6.1.6.3.1.1.4.1.0 = .1.3.6.1.4.1.2021.13.990.0.17 ; .1.3.6.1.2.1.1.6.0 = Argument 1 ; .1.3.6.1.6.3.18.1.3.0 = 127.0.0.1 ; .1.3.6.1.6.3.18.1.4.0 = "public" ; .1.3.6.1.6.3.1.1.4.3.0 = .1.3.6.1.4.1.2021.13.990'
        event = transformer.transform(str)

        assert event["host_address"] == "127.0.5.1"
        assert event["host_name"] == "testhost.localdomain"

        assert event["message"] == "Argument 1"
        
        