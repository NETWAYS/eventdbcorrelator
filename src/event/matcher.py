
from pyparsing import alphas, Word


class Matcher(object):
    
    def __init__(self,definition):
        self.__parseDefinition(definition)
        pass
    
    def __parseDefinition(self,defString):
        operator = ""
    
    def matches(self, event):
        return True