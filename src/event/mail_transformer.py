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
from email.parser import FeedParser
from email import Message
import event
import matcher
import email
import os
import time
import threading
import ConfigParser

MAGIC_FIELDS = ["ignore"]

class GracefulMessageFacade(object):
    """ Facade for the email message object (or any dict) that
        returns "" instead of None for non existing fields and the payload for the message field

    """
    def __init__(self, basedict = None):

        if basedict:
            self.basedict = basedict
        else:
            self.basedict = Message()

    def __getitem__(self, item):
        """ Interface for the feed values. 'message' returns the payload, date a timestamp

        """
        if item.lower() == "message":
            return self.basedict.get_payload().strip()
        if item.lower() == "date":
            return time.mktime(email.utils.parsedate(self.basedict["Date"]))

        if self.basedict.has_key(item):
            return self.basedict[item]

        if self.basedict.has_key(item.lower()):
            return self.basedict[item]

        if self.basedict.has_key(item.upper()):
          return self.basedict[item]

        return ""

    def __setitem__(self, key, value):
        """ Overwrites mail feed values

        """
        self.basedict[key] = value


class MailTransformer(object):
    """ Transformer that takes a raw multiline string like postfix receives them and
        creates an event out of them, according to the rules file defined in the processors
        setup directives

    """


    def __init__(self):
        self.lock = threading.Lock()
        self.rules = []

    def setup(self, instance_id, config):
        """ Sets up this transformer, rules is mandatory

        """

        self.id = instance_id
        if not "rules" in config:
            raise Exception("Mailtransformer %s needs the rules directive to work properly" % instance_id)
        self.read_rules(config["rules"])

    def read_rules(self, file_name):
        """ Reads the rule definitions from the provided file name (if the file exists). If the file doesn't exist
            an exception is thrown

        """

        if not os.path.exists(file_name):
            raise Exception("Could not set up mailtransformer %s: Non existing/not readable mail rule file %s" % (self.id, file_name))
        hdl = open(file_name)
        try:
            parser = ConfigParser.ConfigParser()
            parser.readfp(hdl)

            for section in parser.sections():
                items = parser.items(section)

                # Check if the rule has the ignore flag set
                if not parser.has_option(section,"ignore"):
                    items.append(("ignore",False))
                else:
                    items.append(("ignore",True))

                item_dict = {}
                for item in items:
                    item_dict[item[0]] = item[1]

                # parse default section
                if section.lower() == "default":
                    self.default = item_dict
                    continue

                ev_matcher = matcher.Matcher(section)
                self.rules.append((ev_matcher, item_dict))
        finally:
            hdl.close()

    def transform(self, mailstring):
        """ The mail receiver excepts a multiline string like postfix provides it and extracts/rewrites fields

        """

        feed = self.format_mailfeed(mailstring)
        definition = self.default
        mail_event = event.Event()

        for i in definition:
            mail_event[i] = definition[i]

        for rule in self.rules:
            self.lock.acquire()
            try:
                if rule[0].matches(feed):
                    self.overwrite_event(rule, mail_event, feed)
                    break
            finally:
                self.lock.release()

        if mail_event["ignore"] == True:
            return None
        return mail_event

    def format_mailfeed(self, mailstring):
        """ Returns an email.FeedParser formatted value wrapped by the GracefulMessageFacade class

        """

        reader = FeedParser()
        reader.feed(mailstring)
        message = reader.close()
        return GracefulMessageFacade(message)

    def overwrite_event(self, rule, mail_event, feed):
        """ Overwrites the event according to the rule. the $ and # definitions are used for
            mail values (#) or regexp match groups ($)
        """

        matching_groups = rule[0].get_match_groups()
        for overwrite in rule[1]:
            if overwrite in MAGIC_FIELDS:
                mail_event[overwrite] = rule[1][overwrite]
                continue

            value = rule[1][overwrite]
            if value.startswith("$"):
                value = value[1:]
                if value in matching_groups:
                    mail_event[overwrite] = matching_groups[value]
                else:
                    mail_event[overwrite] = ""
                continue

            if value.startswith("#"):
                value = value[1:]
                mail_event[overwrite] = feed[value]
                continue

            mail_event[overwrite] = rule[1][overwrite]



