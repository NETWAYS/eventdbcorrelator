# Extra tests for the up fnctionality

import unittest
import logging
from event import ip_address

class IPAddressTestCase(unittest.TestCase):
     
    def test_ip4_cidr_syntax(self):
        ip = ip_address.IPAddress("192.168.0.1/24",force_v4=True)
        assert ip.addr == [192,168,0,1]
        assert ip.subnet == [0xFF,0xFF,0xFF,0x00]
        
        ip = ip_address.IPAddress("127.0.0.1/16",force_v4=True)        
        assert ip.addr == [127,0,0,1]
        assert ip.subnet == [0xFF,0xFF,0x00,0x00]
        
        ip = ip_address.IPAddress("127.0.0.1/8",force_v4=True)
        assert ip.subnet == [0xFF,0x00,0x00,0x00]
        
        ip = ip_address.IPAddress("127.0.0.1",force_v4=True)
        assert ip.subnet == []
        
    def test_ip4_cidr_syntax_internal_v6(self):
        ip = ip_address.IPAddress("192.168.0.1/24")
        assert ip.addr == [0,0,0,0, 0,0,0,0, 0,0,0xff,0xff, 192,168,0,1]
        assert ip.subnet == [0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0]
        
        ip = ip_address.IPAddress("127.0.0.1/16")        
        assert ip.addr == [0,0,0,0, 0,0,0,0, 0,0,0xff,0xff, 127,0,0,1]
        assert ip.subnet == [0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0,0]
        
        ip = ip_address.IPAddress("127.0.0.1/8")
        assert ip.subnet == [0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0x0,0x0,0]
        
        ip = ip_address.IPAddress("127.0.0.1")
        assert ip.subnet == []
    
    def test_ip6_cidr_syntax(self):
        ip = ip_address.IPAddress("2001:0db8:85a3:08d3:1319:8a2e:0370:7344/24")
        assert ip.addr == [0x20,0x01,0x0d,0xb8,0x85,0xa3,0x08,0xd3,0x13,0x19,0x8a,0x2e,0x03,0x70,0x73,0x44]
        assert ip.subnet == [0xFF,0xFF,0xFF,0x00,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0]

        ip = ip_address.IPAddress("2001:0db8:85a3::0370:7344/67")
        assert ip.addr == [0x20,0x01,0x0d,0xb8,0x85,0xa3,0,0,0,0,0,0,0x03,0x70,0x73,0x44]
        assert ip.subnet == [0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xE0,0x0,0x0,0x0,0x0,0x0,0x0,0x0]
        
        ip = ip_address.IPAddress("::ffff:127.0.0.1")
        assert ip.addr == [0,0,0,0, 0,0,0,0, 0,0,0xff,0xff,127,0,0,1]
        assert ip.subnet == []
    
    def test_ipv4_in_range(self):
        ip = ip_address.IPAddress("192.168.178.4",force_v4=True)
        
        assert ip.in_range("191.167.0.0","193.169.0.0")
        assert ip.in_range("192.167.0.0","192.169.0.0")
        assert ip.in_range("192.168.0.0","192.168.255.0")
        assert ip.in_range("192.168.178.3","192.168.178.5")
        assert ip.in_range("192.168.178.4","192.168.178.4")
        
        assert ip.in_range("192.168.179.1","192.168.179.3") == False
        assert ip.in_range("10.168.179.1","191.168.179.3") == False

    def test_ipv4_in_range_internal_v6(self):
        ip = ip_address.IPAddress("192.168.178.4")
        
        assert ip.in_range("191.167.0.0","193.169.0.0")
        assert ip.in_range("192.167.0.0","192.169.0.0")
        assert ip.in_range("192.168.0.0","192.168.255.0")
        assert ip.in_range("192.168.178.3","192.168.178.5")
        assert ip.in_range("192.168.178.4","192.168.178.4")
        
        assert ip.in_range("192.168.179.1","192.168.179.3") == False
        assert ip.in_range("10.168.179.1","191.168.179.3") == False
        
        
    def test_ipv6_in_range(self):
        ip = ip_address.IPAddress("2001:0db8:85a3:08d3:1319:8a2e:0370:7344")
        
        assert ip.in_range("2000:0db8:85a3:08d3:1319:8a2e:0370:7344","2002:0db8:85a3:08d3:1319:8a2e:0370:7344")
        assert ip.in_range("2001:0db8:85a3:07d3:1319:8a2e:0370:7344","2001:0db8:85a3:08d3:1319:8a2e:0370:7344")
        assert ip.in_range("::ffff:1.1.1.1","2501:0db8:85a3:08d3:1319:8a2e:0370:7344")
    
    
    def test_ipv4_in_net(self):
        
        ip = ip_address.IPAddress("192.168.178.4",force_v4=True)
        assert ip.in_network("192.168.178.0/24")
        assert ip.in_network("192.168.178.0/29")
        
        ip = ip_address.IPAddress("192.168.178.4/2",force_v4=True)
        assert ip.in_network("192.0.0.0/2")

        ip = ip_address.IPAddress("192.168.178.4",force_v4=True)
        assert ip.in_network("10.0.11.0/4") == False
        assert ip.in_network("192.169.178.0/24") == False
        
        
        ip = ip_address.IPAddress("192.168.67.3")
        assert ip.in_network("192.168.0.0/16")

    def test_ipv6_in_net(self):
        
        ip = ip_address.IPAddress("2001:0db8:85a3:08d3:1319:8a2e:0370:7344/24")
        assert ip.in_network("2001:0d00::/24")
        assert ip.in_network("2001:0d00::/29")
        
    def test_ipv4_in_net_internal_v6(self):
        
        ip = ip_address.IPAddress("192.168.178.4")
        assert ip.in_network("192.168.178.0/24")
        assert ip.in_network("192.168.178.0/29")
        
        ip = ip_address.IPAddress("192.168.178.4/2")
        assert ip.in_network("192.0.0.0/2")

        ip = ip_address.IPAddress("192.168.178.4")
        assert ip.in_network("10.0.11.0/4") == False
        assert ip.in_network("192.169.178.0/24") == False
        
        
        ip = ip_address.IPAddress("192.168.67.3")
        assert ip.in_network("192.168.0.0/16")
        
    def test_ipv4_equality(self):
        ip1 = ip_address.IPAddress("192.168.178.4",force_v4=True)
        ip1_2 = ip_address.IPAddress("192.168.178.4",force_v4=True)
        
        ip2 = ip_address.IPAddress("10.168.178.4",force_v4=True)
        ip2_2 = ip_address.IPAddress("10.168.178.4",force_v4=True)
        
        assert ip1 == ip1_2
        assert ip2 == ip2_2
        assert ip1 != ip2
        
    def test_ipv6_equality(self):
        ip1 = ip_address.IPAddress("2001:0db9:85a3:08d3:1319:8a2e:0370:7344")
        ip1_2 = ip_address.IPAddress("2001:0db9:85a3:08d3:1319:8a2e:0370:7344")
        
        ip2 = ip_address.IPAddress("2001:0db8:85a3:08d3:1319:8a2e:0370:7344")
        ip2_2 = ip_address.IPAddress("2001:0db8:85a3:08d3:1319:8a2e:0370:7344")
        
        assert ip1 == ip1_2
        assert ip2 == ip2_2
        assert ip1 != ip2
        
    def test_ipv4_equality_internal_v6(self):
        ip1 = ip_address.IPAddress("192.168.178.4")
        ip1_2 = ip_address.IPAddress("192.168.178.4")
        
        ip2 = ip_address.IPAddress("10.168.178.4")
        ip2_2 = ip_address.IPAddress("10.168.178.4")
        
        assert ip1 == ip1_2
        assert ip2 == ip2_2
        assert ip1 != ip2
        
    def test_ipv4_from_binary(self):
        ip1 = ip_address.IPAddress("192.168.178.4",force_v4=True)
        ip1_2 = ip_address.IPAddress(ip1.bytes,binary=True,force_v4=True)
        assert ip1 == ip1_2
        
    def test_ipv6_from_binary(self):
        ip1 = ip_address.IPAddress("2001:0db8:85a3:08d3:1319:8a2e:0370:7344")
        ip1_2 = ip_address.IPAddress(ip1.bytes,binary=True)
        assert ip1 == ip1_2
        
    def test_ipv4_from_binary_internal_v6(self):
        ip1 = ip_address.IPAddress("192.168.178.4")
        ip1_2 = ip_address.IPAddress(ip1.bytes,binary=True)
        assert ip1 == ip1_2