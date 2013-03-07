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
import unittest
from event import MailTransformer, Matcher
MAIL_1 = """From moja@ws-jmosshammer.localhost  Wed Jan  2 09:55:05 2013
Return-Path: <moja@ws-jmosshammer.localhost>
X-Original-To: eventdb@localhost
Delivered-To: eventdb@localhost.localhost
Received: by ws-jmosshammer.localhost (Postfix, from userid 541)
 id 28B263AF284; Wed,  2 Jan 2013 09:55:05 +0100 (CET)
Message-Id: <20130102085505.28B263AF284@ws-jmosshammer.localhost>
Date: Wed,  2 Jan 2013 09:55:03 +0100 (CET)
From: moja@localhost (Jannis Mosshammer)

test
"""

MAIL_2 = """From test@testhost  Wed Jan  2 09:55:05 2013
Return-Path: <test@testhost>
X-Original-To: eventdb@localhost
Delivered-To: eventdb@localhost
Received: by test.test (Postfix, from userid 432)
 id 28B263AF284; Wed,  2 Jan 2013 09:55:05 +0100 (CET)
Message-Id: <20130102085505.28B263AF284@test@testhost>
Date: Wed,  2 Jan 2013 09:55:03 +0100 (CET)
From: sender@remote.host (Test)

test_2
"""


class MailTransformerTest(unittest.TestCase):
    """ Tests transformation of mail strings in events

    """

    def test_mail_parsing(self):
        """ Tests if the mail parser works correctly (this is a email.FeedParser with an additional facade object to
            allow matchers to work on raw feed objects)

        """
        transformer = MailTransformer()
        message = transformer.format_mailfeed(MAIL_1)
        assert message["FROM"] == message["from"] == message["From"] ==  "moja@localhost (Jannis Mosshammer)"
        assert message["Date"] == message["date"] == message["DATE"] == 1357116903.0
        assert message["Message"] == message["message"] == message["MESSAGE"] == "test"

    def test_event_creation(self):
        """ Tests if events are correctly created from raw mail strings

        """

        transformer = MailTransformer()
        transformer.rules = [(Matcher("FROM CONTAINS 'localhost'"), {
            "host_name" :   'test_123',
            "message"   :   '#message'
        })]
        transformer.default = {
            "host_name" : 'default',
            "facility"  : 1,
            "priority"  : 2
        }
        event = transformer.transform(MAIL_1)
        assert event["host_name"] == "test_123"
        assert event["message"] == "test"
        assert event["facility"] == 1
        assert event["priority"] == 2

    def test_ignore_event(self):
        """ Tests if the ignore flag works properly and is overwritten from the default values

        """

        transformer = MailTransformer()
        transformer.rules = [(Matcher("FROM CONTAINS 'localhost'"),{
            "host_name" :   'test_123',
            "message"   :   '#message',
            "ignore"    :   False
        })]
        transformer.default = {
            "host_name" : 'default',
            "facility"  : 1,
            "priority"  : 2,
            "ignore"    : True
        }
        mail_event = transformer.transform(MAIL_2)
        assert mail_event == None
        mail_event = transformer.transform(MAIL_1)
        assert mail_event != None

    def test_config_parsing(self):
        """ Just tests if configurations are read properly

        """
        pass
        #transformer = MailTransformer()
        #transformer.setup('test', {"rules": 'src/tests/mailtest.def'})
        #assert len(transformer.rules) == 1
