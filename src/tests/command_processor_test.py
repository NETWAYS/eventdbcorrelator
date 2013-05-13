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
import sys
from processors import CommandProcessor
import logging

PIPE_LOCATION = "/tmp/test.pipe"

class CommandProcessorTest(unittest.TestCase):
    """ Several Tests for the command processor
    """
        
    def remove_temporary_file(self):
        """ Removes the test pipe
        """
        try:
            os.unlink(PIPE_LOCATION)
        except:
            pass
        
    def test_unformatted_command_submit(self):
        """ Simple plain string to pipe test

        """
        try:
            f = open(PIPE_LOCATION, "w+")

            proc = CommandProcessor()
            proc.setup("test", {
                "pipe": PIPE_LOCATION,
                "format" : "Plain string"
            })
            event1 = {
                "message" : 'Testmessage',
                "priority" : 1,
                'anotherfield' : 5
            }
            proc.process(event1)
            f.seek(0)

            assert f.readline().endswith("Plain string\n")
        finally:
            self.remove_temporary_file()
            
    
    def test_formatted_command_submit(self):
        """ Tests $ and # substitution

        """
        try:
            f = open(PIPE_LOCATION,"w+")

            proc = CommandProcessor()
            proc.setup("test",{
                "pipe": PIPE_LOCATION,
                "matcher" : "message REGEXP 'Testmessage from host (?P<HOST>\w+) received'",
                "format" : "#priority : #anotherfield - $HOST"
            })
            event1 = {
                "message" : 'Testmessage from host test123 received',
                "priority" : 1,
                'anotherfield' : 5
            }
            proc.process(event1)
            f.seek(0)
            line = f.readline()
            assert line.endswith("1 : 5 - test123\n")
        finally:
            self.remove_temporary_file()
            
        
    def test_formatted_command_submit_uc(self):
        """ Tests $ and # substitution with uppercase conversion
        """

        try:
            f = open(PIPE_LOCATION,"w+")

            proc = CommandProcessor()
            proc.setup("test",{
                "pipe": PIPE_LOCATION,
                "matcher" : "message REGEXP 'Testmessage from host (?P<HOST>\w+) received'",
                "format" : "#priority : #anotherfield - $HOST",
                "uppercasetokens": True
            })
            event1 = {
                "message" : 'Testmessage from host test123 received',
                "priority" : 1,
                'anotherfield' : 5
            }
            proc.process(event1)
            f.seek(0)
            line = f.readline()
            assert line.endswith("1 : 5 - TEST123\n")
        finally:
            self.remove_temporary_file()

    def test_ssh_command_submit_default_user(self):
        try:
            f = open(PIPE_LOCATION,"w+")
            proc = CommandProcessor()
            proc.setup("test",{
                "pipe": PIPE_LOCATION,
                "matcher" : "message REGEXP 'Testmessage from host (?P<HOST>\w+) received'",
                "format" : "#priority : #anotherfield - $HOST",
                "uppercasetokens": True,
                "use_ssh" : True,
                "ssh_bin" : "echo",
                "remote_address" : 'localhost'
            })

            event1 = {
                "message" : 'Testmessage from host test123 received',
                "priority" : 1,
                'anotherfield' : 5
            }

            proc.process(event1)
            assert proc.remote_address == "localhost"
            assert proc.remote_user == os.getlogin()
            assert proc.remote_port == "22"

        finally:
            self.remove_temporary_file()