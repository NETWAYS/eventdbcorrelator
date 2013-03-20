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
import os
import re
import time
from event import Event
import logging

STATIC_OIDS = {
    ".1.3.6.1.6.3.18.1.3.0"     : "ipaddress",
    ".1.3.6.1.6.3.18.1.4.0"     : "community",
    ".1.3.6.1.6.3.1.1.4.3.0"    : "enterprise",
    # Those are defined, but won't be used for now (we're not an agent)
    ".1.3.6.1.6.3.10.2.1.1.0"   : "securityEngineID",
    ".1.3.6.1.6.3.18.1.1.1.3"   : "securityName",
    ".1.3.6.1.6.3.18.1.1.1.4"   : "contextEngineID",
    ".1.3.6.1.6.3.18.1.1.1.5"   : "contextName"
}

STATIC_STRING_REPLACEMENTS = {
    "$$" : "$",
    "$Ff" : unichr(12),
    "$Fn" : "\r\n",
    "$Fr" : unichr(13),
    "$Ft" : unichr(9)
}

FIELD_NAME_REPLACEMENTS = {
    "$R" : "host_name",
    "$r" : "host_name",
    "$aR" : "ipaddress",
    "$ar" : "ipaddress",
    "$Be" : "securityEngineID",
    "$Bu" : "securityName",
    "$BE" : "contextEngineID",
    "$Bn" : "contextName",
    "$c" : "category",
    "$C" : "community",
    "$o"  : "oid",
    "$s" : "severity",
    "$T" : "uptime"
    
}

DEFAULT_PRIO_MAP = {
   'emer'  :  0,
   'aler'  :  1,
   'crit'  :  2,
   'majo'  :  2,
   'erro'  :  3,
   'warn'  :  4,
   'noti'  :  5,
   'mino'  :  5,
   'ok'    :  5,
   'info'  :  6,
   'norm'  :  6,
   'debu'  :  7
}

class SnmpTransformer(object):
    """ SNMP Receptor class that creates a simple snmp handler which forwards traps to a normal
        edbc pipe. Has some, but not all features of snmptt and is able to parse snmptt mib files
        in order to format traps properly

    """

    
    def setup(self, instance_id, config):
        """ Processor setup method called by the InstanceFactory to apply configuration settings

        """
        self.id = instance_id
        if not "mib_dir" in  config:
            raise Exception("mib_dir directive is missing in %i, this should point to the directory of your snmpttconvertmib files")

        if "trap_format" in config:
            self.trap_format = config["trap_format"]
        else: 
            self.trap_format = "HOST:(?P<HOST>.*);IP:(?P<IP>.*);VARS:(?P<VARS>.*)"

        if "strip_domain" in config:
            self.domains = config["strip_domain"].split(",")
        else:
            self.domains = []

        self.mib_dir = config["mib_dir"]
        self.ip_regexp = re.compile(r"\[(.*?)\]")
        self.trap_matcher = re.compile(self.trap_format)
        self.fixed = {}
        
        if "fixed" in config:
            fixed = config["fixed"].split(",")
            for keyval in fixed:
                keyval = keyval.split("=")
                self.fixed[keyval[0].lower()] = keyval[1]

        self.priorities = {}
        if "prioritymap" in config:
            prios = config["prioritymap"].split(",")
            for sevprio in prios:
                (severity, priority) = keyval.split("=")
                self.priorities[severity] = priority
        else:
            self.priorities = DEFAULT_PRIO_MAP
        
        self.parse_mibs()

    
    def parse_mibs(self):
        """ Reads snmptt mib files from the given mib_dir folder and parses them

        """
        if not os.path.exists(self.mib_dir):
            raise Exception("mib_dir folder %s for %s is not existing/readable " % (self.mib_dir, self.id))
        self.registered_mibs = []
        for mibdir in os.walk(self.mib_dir):
            for mibfile in mibdir[2]:
                if not mibfile.endswith("conf"):
                    continue
                else:
                    self.load_mib(os.path.join(mibdir[0],mibfile))
        
        logging.debug("%s registered %i oids ", self.id, len(self.registered_mibs))
        if len(self.registered_mibs) < 1:
            logging.warn("Warning: %s couldn't find any event definitions registered underneath %s, no events will be persisted", self.id, self.mib_dir)

    
    def _parse_event_line(self, line, mib):
        """ Reads the EVENT line from a snmpttconvertmib generated mib file

        """
        groups = re.match(r"EVENT (?P<EVENT_NAME>[^ ]+) (?P<OID>[0-9\.\*]+) \"(?P<CATEGORY>[\w ]+)\" (?P<EVENT_SEVERITY>\w+)", line)
        if groups:
            groups = groups.groupdict()
            mib["event_name"] = groups["EVENT_NAME"]
            mib["oid"] = groups["OID"]
            mib["category"] = groups["CATEGORY"]
            mib["severity"] = groups["EVENT_SEVERITY"]
            mib["priority"] = self.get_priority_for(mib["severity"])

   

    def get_priority_for(self, severity):
        """ Returns the priority mapped to an event specific severity

        """
        severity = severity.lower()
        for key in self.priorities:
            if severity[0:len(key)] == key.lower():
                return self.priorities[key]
        return None

    def _parse_format_line(self, line, mib):
        """ Read the format line of a snmpttconvertmib generated mib file

        """
        groups = re.match("FORMAT (?P<FORMAT>.*)", line)
        if groups:
            mib["format"] = groups.groupdict()["FORMAT"]    

        for field in STATIC_STRING_REPLACEMENTS:
            mib["format"] = mib["format"].replace(field, STATIC_STRING_REPLACEMENTS[field])
        
    
    def load_mib(self, path):
        """ Load the mib file defined at path

        """
        mibfile = open(path)
        mibs = self.parse_file(mibfile)
        mibfile.close()
        for mib in mibs:
            if "oid" in mib:
                self.registered_mibs.append(mib)
    
    
    def parse_file(self, lines):
        """ PArses a fileobject or an array if strings (representing lines in the mib) as a snmpttconvertmib mib file

        """
        # It doesn't matter if 'lines' is a FileObject or just an array,
        # this makes testing easier
        mibs = []
        mib = {}
        for line in lines:
            if line.strip().startswith("#"):
                continue
            if line.startswith("EVENT"):
                if "oid" in mib:
                    mibs.append(mib)
                    mib = {}
                self._parse_event_line(line, mib)
                continue
            if line.startswith("FORMAT"):
                self._parse_format_line(line, mib)
            if line.startswith("REGEX"):
                self._parse_regexp_expression(line, mib)
        mibs.append(mib)
        return mibs
    
    
    def transform(self, string):
        """ Transformer method as called by the receptor - Transforms a raw snmptt trap to an Event object 

        """
        logging.debug("Raw snmp event: %s", string);
        groups = self.trap_matcher.match(string)
        if not groups:
            logging.debug("String %s didn't match the expected format ", string)
            return None
        event = Event()
        groups = groups.groupdict()
        
        for i in self.fixed:
            event[i] = self.fixed[i]

        event["host_name"] = groups["HOST"]
        for domain in self.domains:
            if(event["host_name"].endswith(domain)):
                event["host_name"] = event["host_name"].partition(domain)[0].strip(".")
                break

        if groups["IP"].startswith("UDP") or groups["IP"].startswith("TCP"):
            event["host_address"] = self.ip_regexp.search(groups["IP"]).group(1)
            logging.debug("IP is %s", event["host_address"])
        
        
        mib_vars = groups["VARS"].split(" ; ")
        expected = ["uptime", "oid"]
        meta = {"host_name" : groups["HOST"]}
        variables = []
        
        for var in mib_vars:
            (oid,value) = var.split(" = ")
            event["snmp_var_"+oid] = value
            if expected:
                meta[expected.pop(0)] = value
                continue
            if oid in STATIC_OIDS:
                meta[STATIC_OIDS[oid]] = value
                continue
            variables.append((oid, value))

        mib = self.get_mib_for(meta["oid"])
        if not mib:
            logging.debug("No mib found for %s ", meta["oid"])
            return None
        event["priority"] = mib["priority"]
        event["created"] = time.ctime()
        event["message"] = self.get_formatted_message(meta, variables, mib)
        logging.debug("Received SNMP trap: %s",event.data)
        return event

    def get_formatted_message(self, meta, variables,mib):
        """ Formats the message according to the FORMAT line in the snmptt mib

        """
        mibformat = mib["format"]
        for i in FIELD_NAME_REPLACEMENTS:
            field_to_replace = FIELD_NAME_REPLACEMENTS[i]
            if field_to_replace in meta:
                mibformat = mibformat.replace(i, meta[field_to_replace])
                
        mibformat = mibformat.replace("$X", str(time.time()))
        mibformat = mibformat.replace("$@", str(time.time()))
        mibformat = mibformat.replace("$x", time.strftime("%x", time.localtime()))
        mibformat = self.replace_variable_expressions(mibformat, variables)
        if "regexp" in mib:
            mibformat = self._apply_regular_expressions(mib["regexp"],mibformat)

        return mibformat

    def replace_variable_expressions(self, mibformat, variables):
        """ Substitutes variable definitions as snmptt does

        """
        mibformat = mibformat.replace("$#", str(int(len(variables))))
        mibformat = mibformat.replace("$*", " ".join(map(lambda x : x[1], variables)))
        mibformat = mibformat.replace("$+*", " ".join(map(lambda x : "%s:%s" % x, variables)))
        
        for i in range(1, len(variables)+1):
            mibformat = mibformat.replace("$%i" % i, variables[i-1][1])
            mibformat = mibformat.replace("$+%i" % i, "%s:%s" % variables[i-1])
            mibformat = mibformat.replace("$v%i" % i, variables[i-1][0])
        
        return mibformat

    def _apply_regular_expressions(self,regexps, mibformat):
        """ Applies all regexs defined in the mib

        """
        for regexp in regexps:
            try:
                mibformat = re.sub(regexp[0], regexp[1], mibformat,count=regexp[2])
            except re.error, regexp_error:
                logging.warn("Regular expression %s is invalid and ignored (error: %s).", regexp, regexp_error)
        return mibformat

    def _parse_regexp_expression(self, regexp, mib):
        """ Parses the regexp line from snmpttconvertmib files
        """
        if not "regexp" in mib:
            mib["regexp"] = []
        groups = re.match(r" *REGEX *\((?P<SEARCH>.*)\)\((?P<REPLACE>.*)\)(?P<FLAGS>[ig]{0,1}) *", regexp)
        if groups == None:
            logging.warn("Invalid Regular expression line '%s#. Ignoring this line", regexp)
            return

        group_dict = groups.groupdict()
        count = 1
        if group_dict["FLAGS"] != "":
            if "i" in group_dict["FLAGS"]:
                group_dict["SEARCH"] = "(?i)%s" % group_dict["SEARCH"]
            if "g" in group_dict["FLAGS"]:
                count = 0


        mib["regexp"].append((group_dict["SEARCH"], group_dict["REPLACE"],count))

	 	
 
    def get_mib_for(self, oid):
        """ Returns the mib defined for the snmp oid or None if the trap is unknown

        """
        for mib in self.registered_mibs:
            if not "oid" in mib:
                logging.warn("No oid registered for mib %s", mib)
                continue
            if re.match("^%s$" % mib["oid"], oid):
                return mib
        
        return None
    
    
