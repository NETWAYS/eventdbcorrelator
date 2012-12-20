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

class StringTransformer(object):
    """ Transforms strings to events using regular expression groups

    """

    def setup(self, id, config):
        """ default processor setup method

        """
        self.id = id
        self.format = re.compile(config["format"])
        if "defaultmessage" in config:
            self.defaultMessage = config["defaultMessage"]
        else:
            self.defaultMessage = "No message given"
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
    
    def set_current_year(self, time_struct):
        """ Returns a new time struct from the given time_struct with the current year set.
            This is needed in case no year is given by an event definition

        """

        now = time.localtime()
        return (now[0], time_struct[1], time_struct[2], time_struct[3], time_struct[4], time_struct[5], time_struct[6], time_struct[7], time_struct[8])
    
    def transform(self,string):
        """ Transforms string to an event using thre regular expression defined in 'format' and
            the fixed values defined in 'fixed'

        """

        try:
            matches =  self.format.match(string)
            if matches == None:
                return None

            matchdict = matches.groupdict()
            return self.dict_to_event(matchdict) 
        except Exception, e:
            logging.warn(e)
    
       
 
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
            matchdict["MESSAGE"] = self.defaultMessage
        
        event = Event(matchdict["MESSAGE"], matchdict["DATE"], matchdict)
        return event
    
    
