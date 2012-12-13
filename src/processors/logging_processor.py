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
import logging

class LoggingProcessor(object):
    """
    Simple processor that only logs to stdout, mainly used for developing or debugging
    """


    def setup(self, id, config):
        self.id = id
        pass
    
    def process(self, event):
        """ Logs a debug statement with the main event fields
        """
        logging.debug("Event : msg=%s host=%s host_addr=%s prio:%s facility:%s ", event["message"], event["host"], event["host_address"], event["priority"], event["facility"])
        