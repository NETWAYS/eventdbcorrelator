import unittest
import os
from receptors.snmp_receptor import SnmpReceptor

class TransformMock(object): 
    def transform(self, string):
        return string
       
'''
SNMP receptors are just creating proxy programs that
write snmp traps to a pipe, from there on its the same
like PipeReceptors
'''
class SNMPReceptorTest(unittest.TestCase):
    
    def test_snmp_setup(self):
        snmp = SnmpReceptor()
        snmp.setup("test", {
            "handler" : "/tmp/snmp_trap",
            "noThread" : True,
            "transformer": TransformMock()
        })
        assert os.path.exists("/tmp/snmp_trap.pipe")
        snmp.start(None, lambda me: me.stop())
        snmp.stop()            
        assert os.path.exists("/tmp/snmp_trap")
        
