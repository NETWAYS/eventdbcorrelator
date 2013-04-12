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
from network.address_resolver import DynamicAddressResolver

class NameResolutionTestCase(unittest.TestCase):

    def test_ip_to_name_dynamic(self):
        resolver = DynamicAddressResolver()
        assert resolver.get_hostname("127.0.0.1") == "localhost"
        assert resolver.get_hostname("127.0.0.15") == "127.0.0.15"
        assert resolver.get_hostname("555.0.0.15") == "555.0.0.15"
        assert resolver.get_hostname("test") == "test"

    def test_name_to_ip_dynamic(self):
        resolver = DynamicAddressResolver()
        assert resolver.get_ip_address("localhost") == "127.0.0.1"
        assert resolver.get_ip_address("idontexistinthenetwork") == "idontexistinthenetwork"
