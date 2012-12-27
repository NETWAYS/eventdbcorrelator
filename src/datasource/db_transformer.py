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
class DBTransformer(object):
    """ Transforms Event OBjects to dictionaries that fit the database schema

    """

    def transform(self, event):
        """ Transforms an event according to it's type. Event types can either
            strings or numeric values

        """
        if event["source"] == "snmp":
            return self.transform_snmp(event)
        if event["source"] == "syslog":
            return self.transform_syslog(event)
        if event["type"]:
            return self.transform_syslog(event, event["type"])
    
    def transform_snmp(self, event):
        """ Transforms a snmp event for the database.
            Facility and type is hardcoded to 1 here.
        """
        return {
            "host_name" : event["host_name"],
            "host_address" : event["host_address"].bytes,
            "type" : 1,
            "facility" : 1,
            "priority" : event["priority"],
            "program" : event["program"],
            "message" : event["message"],
            "ack"     : event["ack"],
            "created" : event["created"],
            "modified": event["modified"]
            
        }

    def transform_syslog(self, event, nr=0):
        """ Transforms a syslog compatible event for the database.
        """
        return {
            "host_name" : event["host_name"],
            "host_address" : event["host_address"].bytes,
            "type" : nr,
            "facility" : event["facility"],
            "priority" : event["priority"],
            "program" : event["program"],
            "message" : event["message"],
            "ack"     : event["ack"],
            "created" : event["created"],
            "modified": event["modified"]
        }
        
    def transform_mail(self,event):
        """ Stub, not implemented yet
        """
        pass
