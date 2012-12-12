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
import logging
from event.event import Event
from receptors.pipe_receptor import PipeReceptor

class TransformMock(object):
    """ Simple transformer mock that does nothing
    
    """
    def transform(self, string):
        return string
        
class PipeReceptorTestCase(unittest.TestCase):
    """ Tests for the pipereceptor input receptor

    """


    def setUp(self):
        """ Unit test setup

        """
        self.TEST_EVENTS = './tests/logtest.syslog'
        self.TESTPATH = '/tmp/test.pipe'

    def test_pipe_setup(self):
        """ Test simple setup and if the pipe created and cleared correctly

        """
        pr = PipeReceptor()
        pr.setup("test",{
            "path": self.TESTPATH,
            "noThread": True, # Receptor must be non-threading
            "transformer": TransformMock()
        })
        assert os.path.exists(self.TESTPATH) == True

        # Nonblocking Pipe, otherwise the test would hang
        pr.run_flags = pr.run_flags | os.O_NONBLOCK
        
        pr.start(None, lambda me: me.stop())
        pr.stop()
        
        assert os.path.exists(self.TESTPATH) == False

    def test_pipe_read(self):
        """ Test if the pipe correctly reads strings from the pipe and recognises line breaks

        """
        pr = PipeReceptor()
        pr.setup("test",{
            "path": self.TESTPATH,
            "transformer": TransformMock()
        })
        queue = Queue.Queue()
        pr.start(queue)
        assert os.path.exists(self.TESTPATH) == True
        pipeFd = os.open(self.TESTPATH, os.O_WRONLY)
        
        teststring = "Hello this is a teststring"
        os.write(pipeFd, teststring+"\n")
        os.write(pipeFd, teststring+"\n")
        queueString = ""
        try:
            queueString = queue.get(True, 2)
        except:
            pass
        
        pr.stop()
        assert queueString == teststring
    
    def test_pipe_multi_read(self):
        """ Test if a pipe is able to write in multiple queues

        """
        pr = PipeReceptor()
        pr.setup("test",{
            "path": self.TESTPATH,
            "transformer": TransformMock()
        })
        queue1 = Queue.Queue()
        queue2 = Queue.Queue()
        queue3 = Queue.Queue()
        queue4 = Queue.Queue()
        pr.start([queue1, queue2])
        pr.register_queue(queue3)
        pr.register_queue(queue4)
        
        assert os.path.exists(self.TESTPATH) == True
        pipeFd = os.open(self.TESTPATH, os.O_WRONLY)
        pr.unregister_queue(queue4)
        teststring = "Hello this is a teststring"
        os.write(pipeFd, teststring+"\n")
        os.write(pipeFd, teststring+"\n")
        queueString = ""
        try:
            queueString1 = queue1.get(True, 2)
            queueString2 = queue2.get(True, 2)
            queueString3 = queue3.get(True, 2)
        except:
            pass
        pr.stop()
        assert queue4.empty()
        assert queueString1 == queueString2 == queueString3 == teststring
    
    def test_pipe_performance(self):
        """ Test if the pipe read performance doesn't break down if there are
            lots of events

        """
        pr = PipeReceptor()
        pr.setup("test",{
            "path": self.TESTPATH,
            "transformer": TransformMock(),
            "bufferSize":64
        })
        queue = Queue.Queue()
        pr.start(queue)
        
        assert os.path.exists(self.TESTPATH) == True
        pipeFd = os.open(self.TESTPATH, os.O_WRONLY)
        testlog = open(self.TEST_EVENTS,"r+")
        try :
            linectr = 0
            bigstr = ""
            for line in testlog:
                linectr = linectr+1
                bigstr = bigstr+line
            os.write(pipeFd, bigstr)
            queueString = ""
            try:
                while linectr > 0:
                    queueString = queueString + queue.get(True, 2)+"\n"
                    linectr = linectr-1
            except:
                pass
            
            assert linectr == 0
            assert len(queueString) == len(bigstr)
            
        finally:            
            testlog.close()
            pr.stop()
            
    def test_pipe_reopen(self):
        """ Test if the pipe is correctly reopened when it's being closed

        """
        pr = PipeReceptor()
        pr.setup("test",{
            "path": self.TESTPATH,
            "transformer": TransformMock(),
            "bufferSize":64
        })
        queue = Queue.Queue()
        testlog = open(self.TEST_EVENTS,"r+")
        linesInFile = 0
        bigstr = ""
        for line in testlog:
            linesInFile = linesInFile+1
            bigstr = bigstr+line
        pr.start(queue)
        try: 
            for i in range(0, 2):
                assert os.path.exists(self.TESTPATH) == True
                pipeFd = os.open(self.TESTPATH, os.O_WRONLY)
                linectr = linesInFile
                os.write(pipeFd, bigstr)
                queueString = ""
                try:
                    while linectr > 0:
                        queueString = queueString + queue.get(True, 2)+"\n"
                        linectr = linectr-1
                except:
                    pass
                
                os.close(pipeFd)
                assert linectr == 0
                assert len(queueString) == len(bigstr)
        finally:            
            testlog.close()
            pr.stop()
        
    def tearDown(self):
        """ Tear down this receptor

        """
        if os.path.exists(self.TESTPATH):
            os.remove(self.TESTPATH)
