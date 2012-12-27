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
import os
from receptors.snmp_receptor import SnmpReceptor

class TransformMock(object):
    """ Mock transformer for Receptor dependencies
    """

    def transform(self, string):
        """ Just returns the input
        """
        return string
       

class SNMPReceptorTest(unittest.TestCase):
    """
    SNMP receptors are just creating proxy programs that
    write snmp traps to a pipe, from there on its the same
    like PipeReceptors, so this is a rather small testunit
    """

    def test_snmp_setup(self):
        """ Test creation of the receptor (trap handler creation, pipe creation)

        """
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
