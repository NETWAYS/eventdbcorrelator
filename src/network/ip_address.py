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
import socket
import logging


class IPAddress(object):
    """ IPAddress class that encapsulates IPv4 and IPv6 addresses and stores 
        them binary. Allows different comparsion operations and uses IPv6 internally
        if not set to force_v4 upon creation

    """    
    
    def __init__(self, ipstring, binary = False, force_v4 =False):
        self.force_v4 = force_v4
        if not binary:
            self.to_bytes(ipstring)
        else:
            self.from_bytes(ipstring)
    
    def to_bytes(self, ipstring):
        """ Converts an ip string to an IPv6 or IPv4 byte array which
            is used internally
 
        """
        cidr_split = ipstring.split("/")
        try:            
            self.bytes = socket.inet_pton(socket.AF_INET, cidr_split[0])
            if socket.has_ipv6 and not self.force_v4:
                if ipstring.startswith("127.0.0.1"):
                    ipstring = ipstring.replace("127.0.0.1","::1")
                else :
                    ipstring = "::ffff:%s" % ipstring
                cidr_split = ipstring.split("/")
                if len(cidr_split) > 1:
                    cidr_split[1] = int(cidr_split[1]) + 96
                self.bytes = socket.inet_pton(socket.AF_INET6, cidr_split[0])
                self.net_len = 128
            else:
                self.net_len = 32
        except socket.error:
            self.bytes = socket.inet_pton(socket.AF_INET6, cidr_split[0])
            self.net_len = 128
        except socket.error:
            raise 'Invalid IP adress'
        self.addr = []
        for i in self.bytes:
            self.addr.append(ord(i))
            
        if len(cidr_split) == 1:
            self.subnet = []
        else:
            self.CIDR_to_subnetmask(int(cidr_split[1]))
    
    def from_bytes(self, ipaddr):
        """ Creates the internal representation from binary data

        """
        self.bytes = ipaddr
        self.addr = []
        for i in self.bytes:
            self.addr.append(ord(i))
       
    def CIDR_to_subnetmask(self, cidr):
        """ Creates a subnetmask from the cidr definition

        """
        self.subnet = []
        for x in range(0, self.net_len/8):
            net = cidr
            if cidr > 8: 
                net = 8
            self.subnet.append((0xff>>(8-net))<<(8-net))
            cidr = cidr-net
            
    def in_range(self, start, end):
        """ Returns true if the address is between the two addresses 
            start or end (start and end can be strings or IPAddress instances)

        """
        start = IPAddress(start, force_v4=self.force_v4)
        end = IPAddress(end, force_v4=self.force_v4)

        for i in range(0, len(self.addr)):
            if self[i] < start[i] or self.addr[i] > end[i]:
                return False            
            if start[i] == end[i]:
                continue
            return True
        return True
    
    def get_network_addr(self):
        """ Returns the network address of this ip address

        """
        if self.subnet == []:
            raise 'get_network_range requires a subnet to be given'
        addr = []
        for i in range(0, len(self.addr)):
            addr.append(self.addr[i] & self.subnet[i])
        return addr
    
            
    def in_network(self, ip):
        """ Returns true when ip is in the same network
            ip can be a IPAddress or a string
        """
        test_ip = IPAddress(ip, force_v4=self.force_v4)
        test_network = test_ip.get_network_addr()
        if self.subnet == []:
            self.subnet = test_ip.subnet
        my_network = self.get_network_addr()

        for i in range(0, len(self.addr)):
            if test_network[i] != my_network[i]:
                return False
        return True
        
    
    def __getitem__(self, nr):
        """ returns the byte at nr

        """
        return self.addr[nr]
    
    
    def __eq__(self, ipaddr):
        """ Equality test, works with IPAddress or raw strings

        """
        if isinstance(ipaddr, str):
            ipaddr = IPAddress(ipaddr)
        for i in range(0, len(self.addr)):
            if ipaddr.addr[i] != self.addr[i]:
                return False
        return True    
        
