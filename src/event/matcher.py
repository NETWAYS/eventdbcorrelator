import re
from matcher_utils import *
class TrueMatcher(object):
    def matches(self,event):
        return True
    
class Matcher(object):
    def __init__(self,definition):
        self.stringTokens = {}
        self.originalString = definition
        self.workingString = definition
        
        self.stringFinder = re.compile('[^\\\]{0,1}(\'.+?\'|".+?")[^\\\]{0,1}',re.IGNORECASE)
        self._parse_definition()
        
   
    def _parse_definition(self):
        self._tokenize_strings()
        self.tree = MatcherTree(self.workingString,self.stringTokens)
        self.tree.compile(PyCompiler(self.stringTokens))
        
        
    def _tokenize_strings(self):
        match = self.stringFinder.findall(self.workingString)
        tokenNr = 0
        for string in match:
            token = "#TOKEN{%i}" % tokenNr
            self.stringTokens[token] = string
            self.workingString = self.workingString.replace(string,token)
            tokenNr = tokenNr + 1

    def matches(self, event):
        return self.tree.test(event)
    
