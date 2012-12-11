import unittest
import os
import Queue
import logging
from event.event import *
from receptors.pipe_receptor import PipeReceptor

class TransformMock(object): 
    def transform(self, string):
        return string
        
class PipeReceptorTestCase(unittest.TestCase):
    def setUp(self):
        self.TEST_EVENTS = './tests/logtest.syslog'
        self.TESTPATH = '/tmp/test.pipe'

    def test_pipe_setup(self):
        pr = PipeReceptor()
        pr.setup("test",{
            "path": self.TESTPATH,
            "noThread": True, # Receptor must be non-threading
            "transformer": TransformMock()
        })
        assert os.path.exists(self.TESTPATH) == True

        # Nonblocking Pipe, otherwise the test would hang
        pr.runFlags = pr.runFlags | os.O_NONBLOCK
        
        pr.start(None, lambda me: me.stop())
        pr.stop()
        
        assert os.path.exists(self.TESTPATH) == False

    
    

    def test_pipe_read(self):
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
        if os.path.exists(self.TESTPATH):
            os.remove(self.TESTPATH)
