import threading
import time
import os
import logging
import re
from event import Matcher, TrueMatcher

class CommandProcessor(object):
    def __init__(self):
        self.lock = threading.Lock()
        
    def setup(self,id,config):
        
        self.id = id
        
        if not "format" in config:
            logging.warn("No format given for CommandProcessor %s, ignoring.",id)
            self.format = None
        else:
            self.format = config["format"]
            
        if not "pipe" in config :
            logging.warn("No pipe given for CommandProcessor %s, ignoring", id)
            self.pipe = None
        else:
            self.pipe = config["pipe"]
            
        if "matcher" in config:
            self.matcher = Matcher(config["matcher"])
        else:
            self.matcher = TrueMatcher()
        
        if "uppercasetokens" in config:
            self.uppercase_tokens = True
        else:
            self.uppercase_tokens = False
        
    def process(self,event):
        if not self.format or not self.pipe:
            return "PASS"
        
        groups = {}
        try:
            self.lock.acquire()
            if not self.matcher.matches(event):
                return "PASS"
            groups = self.matcher.get_match_groups()
        finally:
            self.lock.release()
            
        msg = self.create_notification_message(event,groups)
        msg = "[%i] %s" % (time.time(),msg)
        try:
            self.send_to_pipe(msg)
            return "OK"
        except:
            return "FAIL"
            

    
    def send_to_pipe(self,msg):
        try:
            pipe = os.open(self.pipe,os.O_WRONLY)
            os.write(pipe,msg)
            os.close(pipe)
        except Exception, e:
            logging.error("Could not send command %s to pipe : %s" % (msg,e))
            raise e
    
    def create_notification_message(self,event,matchgroups):
        msg = self.format
        tokens = re.findall("[#$]\w+",msg)
        for token in tokens:
            if token[0] == '#':
                token_tmp = str(event[token[1:]])
                if self.uppercase_tokens:
                    token_tmp = token_tmp.upper()
                msg = msg.replace(token,token_tmp)
                continue
            if token[0] == '$':
                token_tmp = str(matchgroups[token[1:]])
                if self.uppercase_tokens:
                    token_tmp = token_tmp.upper()
                msg = msg.replace(token,token_tmp)
                continue
        if not msg.endswith("\n"):
            msg = msg+"\n"
        return msg
