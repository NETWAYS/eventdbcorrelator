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
import os
import Queue

from receptors import MailReceptor
from pipereceptor_test import TransformMock

TESTPATH = '/tmp/test.pipe'
MAIL_STRINGS = ("""From moja@ws-jmosshammer.localhost  Wed Jan  2 09:55:05 2013
Return-Path: <moja@ws-jmosshammer.localhost>
X-Original-To: eventdb@localhost
Delivered-To: eventdb@localhost.localhost
Received: by ws-jmosshammer.localhost (Postfix, from userid 501)
id 28B263AF284; Wed,  2 Jan 2013 09:55:05 +0100 (CET)
Message-Id: <20130102085505.28B263AF284@ws-jmosshammer.localhost>
Date: Wed,  2 Jan 2013 09:55:03 +0100 (CET)
From: moja@ws-jmosshammer.localhost (Jannis Mosshammer)

test
""","""From moja@ws-jmosshammer.localhost  Wed Jan  2 10:08:24 2013
Return-Path: <moja@ws-jmosshammer.localhost>
X-Original-To: eventdb@localhost
Delivered-To: eventdb@localhost.localhost
Received: by ws-jmosshammer.localhost (Postfix, from userid 501)
id 83B9D3B05EA; Wed,  2 Jan 2013 10:08:24 +0100 (CET)
Message-Id: <20130102090824.83B9D3B05EA@ws-jmosshammer.localhost>
Date: Wed,  2 Jan 2013 10:08:18 +0100 (CET)
From: moja@ws-jmosshammer.localhost (Jannis Mosshammer)

test123
""")
class MailReceptorTest(unittest.TestCase):

    def test_pipe_setup(self):
        """ Test simple setup and if the pipe created and cleared correctly

        """
        pr = MailReceptor()
        pr.setup("test", {
            "path": TESTPATH,
            "noThread": True, # Receptor must be non-threading
            "transformer": TransformMock()
        })
        assert os.path.exists(TESTPATH) == True

        # Nonblocking Pipe, otherwise the test would hang
        pr.run_flags |= os.O_NONBLOCK

        pr.start(None, lambda me: me.stop())
        pr.stop()

        assert os.path.exists(TESTPATH) == False

    def test_mail_reception(self):
        """ Test simple setup and if the pipe created and cleared correctly

        """
        pr = MailReceptor()
        pr.setup("test", {
            "path": TESTPATH,
            "transformer": TransformMock()
        })
        queue = Queue.Queue()
        pr.start(queue)
        try:

            assert os.path.exists(TESTPATH) == True
            for message in MAIL_STRINGS:
                pipeFd = os.open(TESTPATH, os.O_WRONLY)
                os.write(pipeFd, message)
                os.close(pipeFd)

            assert queue.get(timeout=2) == MAIL_STRINGS[0]
            assert queue.get(timeout=2) == MAIL_STRINGS[1]
        finally:
            pr.stop()


