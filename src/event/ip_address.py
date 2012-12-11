import socket
import logging
class IPAddress(object):
    
    def __init__(self, ipstring, binary = False, force_v4 =False):
        self.force_v4 = force_v4
        if not binary:
            self.toBytes(ipstring)
        else:
            self.fromBytes(ipstring)
    
    def toBytes(self, ipstring):
        CIDRsplit = ipstring.split("/")
        try:            
            self.bytes = socket.inet_pton(socket.AF_INET, CIDRsplit[0])
            if socket.has_ipv6 and not self.force_v4:
                ipstring = "::ffff:%s" % ipstring
                CIDRsplit = ipstring.split("/")
                if len(CIDRsplit) > 1:
                    CIDRsplit[1] = int(CIDRsplit[1]) + 96
                self.bytes = socket.inet_pton(socket.AF_INET6, CIDRsplit[0])
                self.net_len = 128
            else:
                self.net_len = 32
        except socket.error:
            self.bytes = socket.inet_pton(socket.AF_INET6, CIDRsplit[0])
            self.net_len = 128
        except socket.error:
            raise 'Invalid IP adress'
        self.addr = []
        for i in self.bytes:
            self.addr.append(ord(i))
            
        if len(CIDRsplit) == 1:
            self.subnet = []
        else:
            self.CIDR_to_subnetmask(int(CIDRsplit[1]))
    
    def fromBytes(self, ipaddr):
        self.bytes = ipaddr
        self.addr = []
        for i in self.bytes:
            self.addr.append(ord(i))
       
    def CIDR_to_subnetmask(self, cidr):
        self.subnet = []
        for x in range(0, self.net_len/8):
            net = cidr
            if cidr > 8: 
                net = 8
            self.subnet.append((0xff>>(8-net))<<(8-net))
            cidr = cidr-net
            
    def in_range(self, start, end):
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
        if self.subnet == []:
            raise 'get_network_range requires a subnet to be given'
        addr = []
        for i in range(0, len(self.addr)):
            addr.append(self.addr[i] & self.subnet[i])
        return addr
    
            
    def in_network(self, ip):
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
        return self.addr[nr]
    
    
    def __eq__(self, ipaddr):
        if isinstance(ipaddr, str):
            ipaddr = IPAddress(ipaddr)
        for i in range(0, len(self.addr)):
            if ipaddr.addr[i] != self.addr[i]:
                return False
        return True    
        
