import urllib
import logging
import re
from network.ip_address import IPAddress


class CheckCommand(object):
    """
    Simple wrapper that receives http-like queries and
    makes them accessible via the subscript operator
    """

    def __init__(self, string):
        self.command_definition = {}
        self.valid = True
        self.parse_message(string)


    def parse_field_host(self, host):
        if host == "":
            return None
        return host.upper()

    def parse_field_facility(self, facility):
        if facility == "" or re.match("^(\d+,{0,1})+$", facility) is None:
            return None
        return map(int, facility.split(','))

    def parse_field_priority(self, priority):
        if priority == "" or re.match("^(\d+,{0,1})+$", priority) is None:
            return None
        return map(int, priority.split(','))

    def parse_field_maxage(self, maxage):
        if maxage == "":
            return None
        return int(maxage)

    def parse_field_message(self, message):
        if message == "":
            return None
        return message

    def parse_field_start_timestamp(self, start_time):
        if start_time == "":
            return None
        return int(start_time)

    def parse_field_program(self, program):
        if program == "":
            return None
        return program.split(',')

    def parse_field_ipaddress(self, ipaddress):
        if ipaddress == "":
            return None
        return IPAddress(ipaddress).bytes

    def parse_field_logtype(self, type):
        if type == "" or re.match("^(\d+,{0,1})+$", type) is None:
            return None
        return map(int, type.split(','))

    def parse_field_prio_warning(self, prios):
        if prios == "" or re.match("^(\d+,{0,1})+$", prios) is None:
            return None
        return map(int, prios.split(','))

    def parse_field_prio_critical(self, prios):
        if prios == "" or re.match("^(\d+,{0,1})+$", prios) is None:
            return None
        return map(int, prios.split(','))


    def parse_field_ack(self, ack):
        if ack == "" or ack != "1":
            return None
        return 1

    def parse_unknown_field(self, field):
        if field == "":
            return None
        return field

    def parse_message(self, string):
        key_value_pairs = string.split("&")
        try:
            for key_value_pair in key_value_pairs:
                (key, value) = key_value_pair.split("=")

                parser = getattr(self,"parse_field_"+key,self.parse_unknown_field)
                self.command_definition[key] = parser(urllib.unquote(value))
        except ValueError, vex:
            logging.warn("Invalid command received: %s (Error is %s)", string, vex.message)
            self.valid = False

    def __getitem__(self, item):
        if not item in self.command_definition:
            return None
        return self.command_definition[item]