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

class SnmpTransformer(object):
    def setup(self,instance_id,config):
        self.id = instance_id
        if not config["mib_dir"]:
            raise "mib_dir directive is missing in %i, this should point to the directory of your snmpttconvertmib files"
        self.mib_dir = config["mib_dir"]
        self.ip_regexp = re.compile("\[(.*)\]")
        self.parse_mibs()
    
    def parse_mibs(self):
        if not os.path.exists(self.mib_dir):
            raise "mib_dir folder %s for %s is not existing/readable " % (self.mib_dir,self.id)
        self.registered_mibs = []
        for dir in os.walk(self.mib_dir):
            for file in dir[2]:
                if not file.endswith("txt") and not file.endswith("mib"):
                    continue
                else:
                    self.load_mib(dir[0]+file)
        
        logging.debug("%s registered %i mibs " % (self.id,len(self.registered_mibs)))
        if len(self.registered_mibs) < 1:
            logging.warn("Warning: %s couldn't find any event definitions registered underneath %s, no events will be persisted" % (self.id, self.mib_dir,))
    
    def parse_event_line(self,line,mib):
        groups = re.match("EVENT (?P<EVENT_NAME>[^ ]+) (?P<OID>[0-9\.\*]+) \"(?P<CATEGORY>[\w ]+)\" (?P<EVENT_SEVERITY>\w+)",line)
        if groups:
            groups = groups.groupdict()
            mib["event_name"] = groups["EVENT_NAME"]
            mib["oid"] = groups["OID"]
            mib["category"] = groups["CATEGORY"]
            mib["severity"] = groups["EVENT_SEVERITY"]
    
    def parse_format_line(self,line,mib):
        groups = re.match("FORMAT (?P<FORMAT>.*)",line)
        if groups:
            mib["format"] = groups.groupdict()["FORMAT"]    

        format = mib["format"] # parse static replacements directly
        for field in STATIC_STRING_REPLACEMENTS:
            mib["format"] = mib["format"].replace(field,STATIC_STRING_REPLACEMENTS[field])
        
    
    def load_mib(self,path):
        file = open(path)
        mib = self.parse_file(file)
        file.close()
        self.registered_mibs.append(mib)
    
    def parse_file(self,lines):
        # It doesn't matter if 'lines' is a FileObject or just an array,
        # this makes testing easier
        mib = {}
        for line in lines:
            if line.strip().startswith("#"):
                continue
            if line.startswith("EVENT"):
                self.parse_event_line(line,mib)
                continue
            if line.startswith("FORMAT"):
                self.parse_format_line(line,mib)
            #ignore rest
        return mib
    
    
    def transform(self,string):
        groups = re.match("HOST:(?P<HOST>.*);IP:(?P<IP>.*);VARS:(?P<VARS>.*)",string)
        if not groups:
            return None
        event = Event()
        groups = groups.groupdict()
        
        event["host_name"] = groups["HOST"]
        if groups["IP"].startswith("UDP") or groups["IP"].startswith("TCP"):
            event["host_address"] = self.ip_regexp.search(groups["IP"]).group(1)
        
        
        vars = groups["VARS"].split(" ; ")
        expected = ["uptime","oid"]
        meta = {"host_name" : groups["HOST"]}
        variables = []
        
        for var in vars:
            (oid,value) = var.split(" = ")
            if expected:
                meta[expected.pop(0)] = value
                continue
            if oid in STATIC_OIDS:
                meta[STATIC_OIDS[oid]] = value
                continue
            variables.append((oid,value))
        mib = self.get_mib_for(meta["oid"])
        if not mib:
            return None
        
        event["created"] = time.time
        event["message"] = self.get_formatted_message(meta,variables,mib)
        return event

    
    def get_formatted_message(self,meta,variables,mib):
        mibformat = mib["format"]
        for i in FIELD_NAME_REPLACEMENTS:
            field_to_replace = FIELD_NAME_REPLACEMENTS[i]
            if field_to_replace in meta:
                mibformat = mibformat.replace(i,meta[field_to_replace])
                
        mibformat = mibformat.replace("$X",str(time.time()))
        mibformat = mibformat.replace("$@",str(time.time()))
        mibformat = mibformat.replace("$x",time.strftime("%x", time.localtime()))
        mibformat = self.replace_variable_expressions(mibformat,variables)
        return mibformat
    
    def replace_variable_expressions(self,mibformat,variables):
        mibformat = mibformat.replace("$#",str(int(len(variables))))
        mibformat = mibformat.replace("$*"," ".join(map(lambda x : x[1],variables)))
        mibformat = mibformat.replace("$+*"," ".join(map(lambda x : "%s:%s" % x,variables)))
        
        for i in range(1,len(variables)+1):
            mibformat = mibformat.replace("$%i" % i,variables[i-1][1])
            mibformat = mibformat.replace("$+%i" % i,"%s:%s" % variables[i-1])
            mibformat = mibformat.replace("$v%i" % i,variables[i-1][0])
        
        return mibformat
        
    def get_mib_for(self,oid):

        for mib in self.registered_mibs:
            if re.match("^%s$" % mib["oid"],oid):
                return mib
        
        return None
        
        