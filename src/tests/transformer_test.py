# To change this template, choose Tools | Templates
# and open the template in the editor.
import unittest
import time
import logging
from event import StringTransformer


class RSyslogTransformerTestCase(unittest.TestCase):

    def setUp(self):
        self.FORMAT = "^(?P<DATE>[a-zA-Z]{2,3} \d\d \d\d:\d\d:\d\d) (?P<HOST>[^ ]+)( (?P<PROGRAM>[^:]+):)? (?P<MESSAGE>.*)$"
        self.LOG_MESSAGES = "./tests/logtest.syslog"
        self.MAX_TIME_PER_EVENT = 0.0001 # Hard limit on how long an incoming event should take on average
        self.rsyslog = [
            ("Sep 21 12:40:02 localhost syslogd 1.4.1: restart.",{
                "DATE" : 1348224002,
                "HOST" : "localhost",
                "PROGRAM" : "syslogd 1.4.1",
                "MESSAGE" : "restart."
            }),
            ("Sep 21 12:40:02 localhost kernel: klogd 1.4.1, log source = /proc/kmsg started.",{
                "DATE" : 1348224002,
                "HOST" : "localhost",
                "PROGRAM" : "kernel",
                "MESSAGE" : "klogd 1.4.1, log source = /proc/kmsg started."
            }),
            ("Sep 21 12:40:07 localhost icinga: The command defined for service SYS_LINUX_SWAP does not exist",{
                "DATE" : 1348224007,
                "HOST" : "localhost",
                "PROGRAM" : "icinga",
                "MESSAGE" : "The command defined for service SYS_LINUX_SWAP does not exist"
            }),
            ("Sep 27 10:08:45 ws-test kernel: [179599.999522] type=1701 audit(1348733325.650:64): auid=4294967295 uid=1000 gid=1000 ses=4294967295 pid=26544 comm=\"chrome\" reason=\"seccomp\" sig=0 syscall=39 compat=0 ip=0x7fd83f0bc6d9 code=0x50001",{
                "DATE" : 1348733325,
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
            logging.debug("RSyslog test: %s " % messageEventPair[0])
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
            logging.debug("Required %s s for %i events (%i s/event)",required,linectr,avg)
            assert required < self.MAX_TIME_PER_EVENT*linectr
            
        finally:
            logfile.close()
        