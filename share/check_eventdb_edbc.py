#! /usr/bin/python
# eventdb (https://www.netways.org/projects/eventdb)
# Copyright (C) 2011 NETWAYS GmbH
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
import pickle

import socket
import time
import re
import sys
import urllib
from optparse import OptionParser


class CheckFilter(object):

    def __init__(self):

        self.logtype = 0
        self.facility = ""
        self.priority = ""
        self.startfrom = 0
        self.maxage = ""
        self.message = ""
        self.startTimestamp = None
        self.prio_critical=""
        self.prio_warning=""
        self.program = ""
        self.ipaddress = ""
        self.host = ""

    def setLogtype(self,type):
        typemap = {
            "syslog" : 0,
            "snmptrap" : 1,
            "mail" : 2
        }
        if not type in typemap :
            raise Exception("Invalid type provided for log-source")
        self.logtype = typemap[type]


    '''
    Sets the maxage by converting the relative maxage format like 4d, 2m, 20h to
    an absolute database timestamp (YYYY-MM-DD HH:MI:SS)
    '''
    def setMaxage(self,maxage):
        if maxage == "":
            return
        curTime = time.time()
        matches = re.match(r"(\d*?)(d|h|m)",maxage)
        matchGroups = matches.groups()
        if(len(matchGroups) != 2):
            raise Exception("Invalid maxage format")

        timeOffset = int(matchGroups[0])
        # modify timestamp to represent the maximum age
        if(matchGroups[1] == 'd'):
            curTime = curTime-timeOffset*86400
        elif(matchGroups[1] == 'h'):
            curTime = curTime-timeOffset*3600
        elif(matchGroups[1] == 'm'):
            curTime = curTime-timeOffset*60

        self.startTimestamp = curTime
        self.maxage = curTime

    def setPerfdata(self,perfdata):
        if perfdata == None:
            return
        idxMatch = re.findall(r'count=(\d+)',perfdata);
        if(len(idxMatch) > 0):
            self.startfrom = int(idxMatch[0])

    def to_query(self):
        query = ""
        queryAttributes = {
            "logtype","facility","priority", "startfrom", "maxage", "message",
            "startTimestamp", "prio_critical", "prio_warning", "program", "ipaddress",
            "host"
        }
        queryParts = []
        for part in queryAttributes:
            if self.__getattribute__(part) is None \
                or self.__getattribute__(part) == "":
                continue;
            queryParts.append("%s=%s" % (part, urllib.quote(str(self.__getattribute__(part)))))
        print queryParts
        return "&".join(queryParts)

'''
check_eventb.py

'''
class CheckStatusException(Exception):
    def __init__(self,status,output,perfdata = ""):
        self.status = status
        self.output = output
        self.perfdata = perfdata


class EventDBPlugin(object):

    def __init__(self,arguments = None):
        if arguments == None:
            self.__options = self.__parseArguments()
        elif isinstance(arguments,object):
            self.__options = arguments;

        self.__prepareArguments()
        self.__runCheck()


    def __prepareArguments(self):
        self.__handleArguments()
        if(self.__options.print_cv):
            print self.__getCVFilter()
            return
        try:
            self.__validateArguments()


        except Exception, e:
            self.__pluginExit("UNKNOWN","Invalid Arguments",e)


    def __runCheck(self):
        options = self.__options

        #try:
        result = self.query_edbc()
        if(result):
            self.__checkResult(result[2],result[3],result[0],result[1],result[4])

        #except Exception, e:
         #   self.__pluginExit("UNKNOWN","An error occured",e)


    def __handleArguments(self):
        options = self.__options

        self.__checkFilter = CheckFilter()
        self.__checkFilter.setLogtype(options.logtype)
        self.__checkFilter.setMaxage(options.maxage)
        self.__checkFilter.setPerfdata(options.perfdata)
        self.__checkFilter.facility = options.facility
        self.__checkFilter.priority = options.priority
        self.__checkFilter.prio_warning = options.prio_warning
        self.__checkFilter.prio_critical = options.prio_critical
        self.__checkFilter.program = options.program
        self.__checkFilter.message = options.message
        self.__checkFilter.host = options.host
        self.__checkFilter.ipaddress = options.ipaddress
        if(self.__options.facility):
            self.__options.facility = self.__options.facility.split(",")
        if(self.__options.priority):
            self.__options.priority = self.__options.priority.split(",")



    def __validateArguments(self):
        if(self.__options.warning == -1 or self.__options.critical == -1):
            raise Exception("warning or critical parameter missing")

    '''
    '   Returns the CustomVariable definition required to add special eventDB filter to the icinga-web
    '   cronk
    '
    '''
    def __getCVFilter(self):
        opts = self.__options
        strTpl = "_edb_filter            {'msg': %s, 'sourceExclusion': [%s],'priorityExclusion': [%s], 'facilityExclusion': [%s], 'startTime': %s }"
        msgFilter = "''"
        sourceExclusion = ""
        priorityExclusion = ""
        facilityExclusion = ""
        timespan = -1
        if opts.message != "":
            msgFilter = "{type:'exact','message' : '%s', isRegexp: false}" % opts.message
        if opts.logtype != "":
            arr = ['0','1','2']
            del arr[opts.logtype]

            sourceExclusion = ",".join(arr)
        if isinstance(opts.priority,list):
            allPrios = ['0','1','2','3','4','5','6','7'];
            priorityExclusion = ",".join(list(set(allPrios)-set(opts.priority)))
        if isinstance(opts.facility,list):
            allFacs = [];
            for i in range(24):
                allFacs.append(str(i))

            facilityExclusion = ",".join(list(set(allFacs)-set(opts.facility)))
        if hasattr(opts,"start_ts") and opts.start_ts != '':
            timespan = opts.start_ts

        return strTpl % (msgFilter,sourceExclusion, priorityExclusion,facilityExclusion,timespan)


    def connect_to_edbc(self):
        connection = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        connection.connect(self.__options.edbc_socket)
        return connection


    def query_edbc(self):
        #try:
        socket = self.connect_to_edbc()
        query = self.__checkFilter.to_query()
        socket.send(query)
        print pickle.loads(socket.recv(2048))
        #except Exception, e:
        #    self.__pluginExit('UNKNOWN', "",e)




    def __checkResult(self,warnings,criticals,count, last,msg = ""):

        #strip newlines from message
        if(msg != "" and isinstance(msg,str)):
            msg= msg.replace('\n',' ')
        if(criticals >= self.__options.critical):
            if(self.__options.resetregex and re.search(self.__options.resetregex,msg)):
                return self.__pluginExit(
                    'OK',
                    "%d critical and %d warning matches found\nMatches found already reseted." % (criticals,warnings),
                    'matches=%d count=%dc' % (count,last)
                )
            else:
                return self.__pluginExit(
                    'CRITICAL',
                    ("%d critical and %d warning matches found\n"+msg) % (criticals,warnings),
                    'matches=%d count=%dc' % (count,last)
                )
        elif(warnings >= self.__options.warning):
            if(self.__options.resetregex  and re.search(self.__options.resetregex,msg)):
                return self.__pluginExit(
                    'OK',
                    "%d critical and %d warning matches found\nMatches found already reseted."% (criticals,warnings),
                    'matches=%d count=%dc' % (count,last)
                )
            else:
                return self.__pluginExit(
                    'WARNING',
                    ('%d critical and %d warning matches found \n,'+msg) % (criticals,warnings),
                    'matches=%d count=%dc' % (count,last)
                )
        else:
            return self.__pluginExit(
                'OK',
                "%d critical and %d warning matches found."%(criticals,warnings),
                "matches=%d count=%dc"%(count,last)
            )

        return self.__pluginExit('UNKNOWN', '0 matches found.\n','Default exit')



    def __pluginExit(self,status,text,perfdata):
        statusCode = {'UNKNOWN' : 3, 'OK' : 0, 'WARNING' : 1, 'CRITICAL' : 2}
        out = ""

        try:
            text = text.replace('|', '')
            text = text.replace('\n', ' ')
        except Exception:
            pass
        out += "%s %s %s" % (status,self.__options.label,text)

        out += '|%s' % perfdata
        out += "\nmessage filter: %s" % self.__options.message
        out += "\nreset regexp: %s" % self.__options.resetregex

        print out
        sys.exit(statusCode[status])



    def __parseArguments(self):
        parser = OptionParser()
        parser.add_option("-H","--host",dest="host",
                        help="Hostname as logged by the agent", default="")
        parser.add_option("-m","--msg",dest="message",
                        help="Message as logged by the agent (SQL Format wildcards)", default="")
        parser.add_option("-f","--facility",dest="facility", default="",
                        help="The facilities to respect, comma separated"),
        parser.add_option("-p","--priority",dest="priority",
                        help="Priority as logged by the agent", default="")
        parser.add_option("-t","--type",dest="logtype",type="choice",default="syslog",
                        help="The logtype (syslog,snmptrap,mail)",choices=["syslog","snmptrap","mail"])
        parser.add_option("-P","--program",dest="program",
                        help="Program as logged by the agent", default="")
        parser.add_option("-W","--warning-priorities",dest="prio_warning",default="",
                        help="A comma seperated set of priorities which will be used for determine the warning state" ),
        parser.add_option("-C","--critical-priorities",dest="prio_critical",default="",
                        help="A comma seperated set of priorities which will be used for determine the warning state" ),
        parser.add_option("-S", "--edbc-socket", dest="edbc_socket", default="/usr/local/edbc/var/edbc_api.sock",
                        help="The location of our edbc api-socket")
        parser.add_option("-l","--label",dest="label",
                        help="Label for plugin output", default="")
        parser.add_option("--maxage",dest="maxage",
                        help="Maximum age of EventDB entry (eg. 1m, 2h, 3d)", default="")
        parser.add_option("-r","--resetregexp",dest="resetregex",
                        help="Regular Expression for message entry in eventdb to change each state back to OK", default="")
        parser.add_option("--perfdata",dest="perfdata",
                        help="Performance data from the last check (e.g. \$SERVICEPERFDATA\$)", default="")
        parser.add_option("-I", "--ip",dest="ipaddress", help="Filter by ip address", default="")
        parser.add_option("-w","--warning",dest="warning",type="int",help="Number of matches to result in warning state",default="-1")
        parser.add_option("-c","--critical",dest="critical",type="int",help="Number of matches to result in critical state",default="-1")
        parser.add_option("--cventry",dest="print_cv", default=False,action="store_true",
                        help="returns the custom variable entry for this call (needed in order to use icinga-web cronk integration)")

        (options, args) = parser.parse_args()
        return options;





def main():
    EventDBPlugin()

if __name__ == "__main__":
    main()

# define service{
#         use                             generic-service
#         host_name                       localhost
#         service_description             eventdb
#          _edb_filter                     {..result From cventry..}
#           # critical for all status other than 4.
#         check_command                   check_eventdb!1!1!%Interesting Status:%!-r Status: 4
#         }
# 'check_eventdb' command definition
#
# define command{
#         command_name            check_eventdb
#         command_line            $USER1$/contrib/check_eventdb.pl --dbuser eventdbrw --dbpassword eventdbrw --url "/nagios/eventdb/index.php" -w $ARG1$ -c $ARG2$ -m "$ARG3$" "$ARG4$"
# }

