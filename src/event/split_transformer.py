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
import re
import logging
import time
from event import Event

class SplitTransformer(object):
    """ Helper class to transform strings, arrays, etc to Event objects

    """


    def setup(self, proc_id, config):
        """ default processor setup method

        """
        self.id = proc_id
        
        if "defaultmessage" in config:
            self.default_message = config["defaultMessage"]
        else:
            self.default_message = "No message given"
        self.fixed = {}
        
        if "fixed" in config:
            fixed = config["fixed"].split(",")
            for keyval in fixed:
                keyval = keyval.split("=")
                self.fixed[keyval[0].lower()] = keyval[1]
        
        if "dateformat" in config:
            self.dateFormat = config["dateformat"]
        else:
            self.dateFormat = "%b %d %H:%M:%S"

        if "delimiter" in config:
            self.delimiter = config["delimiter"]
        else:
            self.delimiter = "\t"
        self.group_order = config["group_order"].split(" ")
        self.nr_of_groups = len(self.group_order)

    
    def set_current_year(self, time_struct):
        """ Returns a new time struct from the given time_struct with the current year set.
            This is needed in case no year is given by an event definition

        """
        now = time.localtime()
        return (now[0], time_struct[1], time_struct[2] ,time_struct[3], time_struct[4], time_struct[5], time_struct[6], time_struct[7], time_struct[8])
 
    def transform(self, string):
        """ Transforms a raw string to an event by splitting it at dthe delimiter and returns the created event

        """
        try:
            dict = {} 

            stringtokens = re.split(self.delimiter, string)
            nr_of_tokens = len(stringtokens)
            tokenrange = range(0, nr_of_tokens)

            if nr_of_tokens != self.nr_of_groups:
                logging.warn("Event has %i properties, expected %i (raw event : %s)", nr_of_tokens, self.nr_of_groups, string)
                if self.nr_of_groups < nr_of_tokens:
                    tokenrange = range(0, self.nr_of_groups) # prevent overflow

            for pos in tokenrange:
                dict[self.group_order[pos]] = stringtokens[pos]

            return self.dict_to_event(dict)
        except Exception, e:
            logging.error("Couldn't transform %s to an event : %s" , string, e)
            return None
 
    def dict_to_event(self, matchdict = {}):
        """ Turns an dict to an Event object and returns it

        """

        for i in self.fixed:
            matchdict[i] = self.fixed[i]
        if not "DATE" in matchdict:
            matchdict["DATE"] = time.ctime()
        else:
            if "TIME" in matchdict:
                matchdict["DATE"] = matchdict["DATE"]+" "+matchdict["TIME"]
            matchdict["DATE"] = time.strptime(matchdict["DATE"],self.dateFormat)
            if matchdict["DATE"][0] < 2000:
                matchdict["DATE"] = self.set_current_year(matchdict["DATE"])
            matchdict["DATE"] = time.mktime(matchdict["DATE"])
    
        if not "MESSAGE" in matchdict:
            matchdict["MESSAGE"] = self.default_message
        
        event = Event(matchdict["MESSAGE"], matchdict["DATE"], matchdict)
        return event
    
    
