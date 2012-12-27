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
from network import ip_address

class IPAddressTestCase(unittest.TestCase):
    """ Several tests for the IPAddress class used in matchers    
    
    """
     
    def test_ip4_cidr_syntax(self)  :
        """ IP4 CIDR

        """

        test_ip = ip_address.IPAddress("192.168.0.1/24", force_v4=True)
        assert test_ip.addr == [192, 168, 0, 1]
        assert test_ip.subnet == [0xFF, 0xFF, 0xFF, 0x00]
        
        test_ip = ip_address.IPAddress("127.0.0.1/16", force_v4=True)        
        assert test_ip.addr == [127, 0, 0, 1]
        assert test_ip.subnet == [0xFF, 0xFF, 0x00, 0x00]
        
        test_ip = ip_address.IPAddress("127.0.0.1/8", force_v4=True)
        assert test_ip.subnet == [0xFF, 0x00, 0x00, 0x00]
        
        test_ip = ip_address.IPAddress("127.0.0.1", force_v4=True)
        assert test_ip.subnet == []
        
    def test_ip4_cidr_syntax_internal_v6(self):
        """ IP4 CIDR with internal IPv6 conversion

        """
 
        test_ip = ip_address.IPAddress("192.168.0.1/24")
        
        assert test_ip.addr == [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0xff, 0xff, 192, 168, 0, 1]
        assert test_ip.subnet == [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0]
        
        test_ip = ip_address.IPAddress("127.0.0.1/16")        
        assert test_ip.addr == [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
        assert test_ip.subnet == [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0, 0]
        
        test_ip = ip_address.IPAddress("127.0.0.1/8")
        assert test_ip.subnet == [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x0, 0x0, 0]
        
        test_ip = ip_address.IPAddress("127.0.0.1")
        assert test_ip.subnet == []
    
    def test_ip6_cidr_syntax(self):
        """ IP6 CIDR 

        """

        test_ip = ip_address.IPAddress("2001:0db8:85a3:08d3:1319:8a2e:0370:7344/24")
        assert test_ip.addr == [0x20, 0x01, 0x0d, 0xb8, 0x85, 0xa3, 0x08, 0xd3, 0x13, 0x19, 0x8a, 0x2e, 0x03, 0x70, 0x73, 0x44]
        assert test_ip.subnet == [0xFF, 0xFF, 0xFF, 0x00, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]

        test_ip = ip_address.IPAddress("2001:0db8:85a3::0370:7344/67")
        assert test_ip.addr == [0x20, 0x01, 0x0d, 0xb8, 0x85, 0xa3, 0, 0, 0, 0, 0, 0, 0x03, 0x70, 0x73, 0x44]
        assert test_ip.subnet == [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xE0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
        
        test_ip = ip_address.IPAddress("::ffff:127.0.0.1")
        assert test_ip.addr == [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0xff, 0xff, 127, 0, 0, 1]
        assert test_ip.subnet == []
    
    def test_ipv4_in_range(self):
        """ IPv4 network range tests

        """

        test_ip = ip_address.IPAddress("192.168.178.4", force_v4=True)
        
        assert test_ip.in_range("191.167.0.0","193.169.0.0")
        assert test_ip.in_range("192.167.0.0","192.169.0.0")
        assert test_ip.in_range("192.168.0.0","192.168.255.0")
        assert test_ip.in_range("192.168.178.3","192.168.178.5")
        assert test_ip.in_range("192.168.178.4","192.168.178.4")
        
        assert test_ip.in_range("192.168.179.1","192.168.179.3") == False
        assert test_ip.in_range("10.168.179.1","191.168.179.3") == False

    def test_ipv4_in_range_internal_v6(self):
        """ IPv4 network range tests, internal IPv6

        """
        test_ip = ip_address.IPAddress("192.168.178.4")
        
        assert test_ip.in_range("191.167.0.0","193.169.0.0")
        assert test_ip.in_range("192.167.0.0","192.169.0.0")
        assert test_ip.in_range("192.168.0.0","192.168.255.0")
        assert test_ip.in_range("192.168.178.3","192.168.178.5")
        assert test_ip.in_range("192.168.178.4","192.168.178.4")
        
        assert test_ip.in_range("192.168.179.1","192.168.179.3") == False
        assert test_ip.in_range("10.168.179.1","191.168.179.3") == False
        
        
    def test_ipv6_in_range(self):
        """ IPv6 network range test

        """
        test_ip = ip_address.IPAddress("2001:0db8:85a3:08d3:1319:8a2e:0370:7344")
        
        assert test_ip.in_range("2000:0db8:85a3:08d3:1319:8a2e:0370:7344","2002:0db8:85a3:08d3:1319:8a2e:0370:7344")
        assert test_ip.in_range("2001:0db8:85a3:07d3:1319:8a2e:0370:7344","2001:0db8:85a3:08d3:1319:8a2e:0370:7344")
        assert test_ip.in_range("::ffff:1.1.1.1","2501:0db8:85a3:08d3:1319:8a2e:0370:7344")
    
    
    def test_ipv4_in_net(self):
        """ IPv4 network containment test

        """
        test_ip = ip_address.IPAddress("192.168.178.4", force_v4=True)
        assert test_ip.in_network("192.168.178.0/24")
        assert test_ip.in_network("192.168.178.0/29")
        
        test_ip = ip_address.IPAddress("192.168.178.4/2", force_v4=True)
        assert test_ip.in_network("192.0.0.0/2")

        test_ip = ip_address.IPAddress("192.168.178.4", force_v4=True)
        assert test_ip.in_network("10.0.11.0/4") == False
        assert test_ip.in_network("192.169.178.0/24") == False
        
        
        test_ip = ip_address.IPAddress("192.168.67.3")
        assert test_ip.in_network("192.168.0.0/16")

    def test_ipv6_in_net(self):
        """ IPv6 network containment test

        """
        test_ip = ip_address.IPAddress("2001:0db8:85a3:08d3:1319:8a2e:0370:7344/24")
        assert test_ip.in_network("2001:0d00::/24")
        assert test_ip.in_network("2001:0d00::/29")
        
    def test_ipv4_in_net_internal_v6(self):
        """ IPv4 network containment test, internal IPv6 conversion

        """
        test_ip = ip_address.IPAddress("192.168.178.4")
        assert test_ip.in_network("192.168.178.0/24")
        assert test_ip.in_network("192.168.178.0/29")
        
        test_ip = ip_address.IPAddress("192.168.178.4/2")
        assert test_ip.in_network("192.0.0.0/2")

        test_ip = ip_address.IPAddress("192.168.178.4")
        assert test_ip.in_network("10.0.11.0/4") == False
        assert test_ip.in_network("192.169.178.0/24") == False
        
        
        test_ip = ip_address.IPAddress("192.168.67.3")
        assert test_ip.in_network("192.168.0.0/16")
        
    def test_ipv4_equality(self):
        """ IPv4 Equality tests

        """
        ip1 = ip_address.IPAddress("192.168.178.4", force_v4=True)
        ip1_2 = ip_address.IPAddress("192.168.178.4", force_v4=True)
        
        ip2 = ip_address.IPAddress("10.168.178.4", force_v4=True)
        ip2_2 = ip_address.IPAddress("10.168.178.4", force_v4=True)
        
        assert ip1 == ip1_2
        assert ip2 == ip2_2
        assert ip1 != ip2
        
    def test_ipv6_equality(self):
        """ IPv6 equality tests

        """
        ip1 = ip_address.IPAddress("2001:0db9:85a3:08d3:1319:8a2e:0370:7344")
        ip1_2 = ip_address.IPAddress("2001:0db9:85a3:08d3:1319:8a2e:0370:7344")
        
        ip2 = ip_address.IPAddress("2001:0db8:85a3:08d3:1319:8a2e:0370:7344")
        ip2_2 = ip_address.IPAddress("2001:0db8:85a3:08d3:1319:8a2e:0370:7344")
        
        assert ip1 == ip1_2
        assert ip2 == ip2_2
        assert ip1 != ip2
        
    def test_ipv4_equality_internal_v6(self):
        """ IPv4 equality tests, internal IPv6 conversion

        """
        ip1 = ip_address.IPAddress("192.168.178.4")
        ip1_2 = ip_address.IPAddress("192.168.178.4")
        
        ip2 = ip_address.IPAddress("10.168.178.4")
        ip2_2 = ip_address.IPAddress("10.168.178.4")
        
        assert ip1 == ip1_2
        assert ip2 == ip2_2
        assert ip1 != ip2
        
    def test_ipv4_from_binary(self):
        """ IPv4 adress from binary test

        """
        ip1 = ip_address.IPAddress("192.168.178.4", force_v4=True)
        ip1_2 = ip_address.IPAddress(ip1.bytes, binary=True, force_v4=True)
        assert ip1 == ip1_2
        
    def test_ipv6_from_binary(self):
        """ IPv4 address from binary test
        
        """
        ip1 = ip_address.IPAddress("2001:0db8:85a3:08d3:1319:8a2e:0370:7344")
        ip1_2 = ip_address.IPAddress(ip1.bytes, binary=True)
        assert ip1 == ip1_2
        
    def test_ipv4_from_binary_internal_v6(self):
        """ IPv4 address from binary test, internal IPv6

        """
        ip1 = ip_address.IPAddress("192.168.178.4")
        ip1_2 = ip_address.IPAddress(ip1.bytes, binary=True)
        assert ip1 == ip1_2

