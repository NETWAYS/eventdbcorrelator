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
import ip_address

class DynamicAddressResolver(object):
    """ Resolver that uses the python socket library for resolving names dynamically

    """

    def get_hostname(self, ip_address):
        try:
            return socket.gethostbyaddr(ip_address)[0]
        except socket.herror:
            return ip_address
        except socket.gaierror:
            return ip_address

    def get_ip_address(self, host, port = None):
        try:
            ip = socket.getaddrinfo(host,port)
            if len(ip) > 0 and len(ip[0]) > 3 and len(ip[0][4]) > 0:
                return ip_address.IPAddress(ip[0][4][0])
            return None
        except socket.herror:
            return host
        except socket.gaierror:
            return host