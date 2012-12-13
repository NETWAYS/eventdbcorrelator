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
from event import Matcher,TrueMatcher
MOD_TARGETS = ["event","group"]

class ModifierProcessor(object):
    """ Modifies an event or a complete event group on the fly

    """

    def setup(self, _id, config):
        """ Setup method that configures the instance of this method

        InstanceFactory calls this with the id and configuration from datasource
        definitions defined in the conf.d directory
        """
        self.id = _id
        self.overwrites = []
        if "overwrite" in config:
            overwrite_keyvals = config["overwrite"].split(";")
            for keyval in overwrite_keyvals:
                self.overwrites.append(keyval.split("="))
        self.target = "event"
        if "target" in config:
            if not config["target"] in MOD_TARGETS:
                logging.warn("Target %s is invalid for ModifierProcessor %s, using 'event' instead", config["target"], self.id)
            else:
                self.target = config["target"]
        
        self.datasource = None
        if "datasource" in config:
            self.datasource = config["datasource"]
                
        self.acknowledge = False
        
        self.matcher = TrueMatcher()
        if "matcher" in config:
            self.matcher = Matcher(config["matcher"])
            
        if "acknowledge" in config:
            if config["acknowledge"] != "false":
                self.acknowledge = True
        
    def process(self, event):
        """ Processes the event if the matcher defined for this processor
            matches
        """
        if not self.matcher.matches(event):
            return "PASS"
        if self.target == "event":
            return self.process_event(event)
        if self.target == "group" and event["group_id"] or event["clear_group_id"]:
            return self.process_group(event)
        
    def process_event(self, event):
        """ Processes only a single event and updates it's properties

        """
        if self.acknowledge:
            event["ack"] = 1
        for (key,val) in self.overwrites:
            event[key] = val
        return "OK"
    
    def process_group(self, event):
        """ Updates a complete process group and queries the db
            Changes will be written to the db upon the next database buffer flush

        """
        if not self.datasource :
            logging.warn("Can't process group without datasource")
            return "PASS"
        query = "UPDATE " + self.datasource.table + " SET "
        glue = ""
        if self.acknowledge:
            query += " ack = 1 "
            glue = ","
        
        for (key,val) in self.overwrites:            
            query += "%s %s = '%s' " % (glue, key, val)
            glue = ","
        group_id = event["group_id"] or event["clear_group_id"]
        group_leader = event["group_leader"] or event["clear_group_leader"]
        query += " WHERE (group_id = %s AND group_leader = %s) OR id=%s "
        self.datasource.execute_after_flush(query, (group_id, group_leader, group_leader))
        return "OK"

