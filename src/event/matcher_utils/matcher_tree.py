import re
from constants import *
from event import ip_address



class MatcherTree(object):
    
    def __init__(self,queryString,tokens):
        self.tokens = tokens
        self._prepare_regexp()
        self.rawTree = self._get_query_node(queryString)
        self.compiled = ""
        self.regex_groups = {}
        self.compiledMatcher = None
        
        
    def _prepare_regexp(self):
        self.conjunctionSplitter = re.compile(" ("+"|".join(CONJUNCTIONS)+") ",re.IGNORECASE)
        self.operatorSplitter = re.compile(" ("+"|".join(EXPRESSION_OPERATORS)+") ",re.IGNORECASE)
    
    
    def is_expression(self,node):
        return node["root"] in EXPRESSION_OPERATORS
    
    def is_conjunction(self,node):
        return node["root"].strip() in CONJUNCTIONS
    
    def regexp_test(self,reg,val):
        groups = re.search(reg,val,re.IGNORECASE)
        if not groups:
            return False
        self.regex_groups = dict(self.regex_groups.items() + groups.groupdict().items())
        return True
    
    def compile(self,compiler):
        self.traverse(self.is_expression,compiler.compile_expression)
        self.traverse(self.is_conjunction,compiler.build_expressions,self.rawTree,True)
        self.compiledMatcher = lambda event : eval(self.rawTree[compiler.COMPILE_ATTR])

    def test(self,event):
        self.regex_groups = {}
        if self.compiledMatcher:
            return self.compiledMatcher(event)
        else:
            return False
        
    def traverse(self,matcherFn=lambda tnode:True,handler=lambda tnode:tnode,node=None,bottomUp=False):
        if node == None:
            node = self.rawTree
        
        # Bottom up parsing
        if self.is_conjunction(node) and bottomUp:
            self.traverse(matcherFn,handler,node["left"],bottomUp)
            self.traverse(matcherFn,handler,node["right"],bottomUp)
        
        if matcherFn(node):
            node = handler(node)
        
        # Top down parsing
        if self.is_conjunction(node) and not bottomUp:
            self.traverse(matcherFn,handler,node["left"],bottomUp)
            self.traverse(matcherFn,handler,node["right"],bottomUp)

    

    def _get_query_node(self,curString):
        groups = self._get_conjunction_groups(curString)
        if len(groups) == 1:
            field,operator,value = self._get_expression(groups[0])
            return {
                "root": operator.upper().strip(),
                "left": field.strip(),
                "right": value.strip()
            }
        if len(groups) > 3: # More than one conjunction at a level, create omitted parenthesis
            groups[2] = "   ".join(groups[2:])
        return {
            "root" : groups[1].strip(),
            "left" : self._get_query_node(groups[0]),
            "right": self._get_query_node(groups[2])
        }

    def _get_conjunction_groups(self,baseString):
        splitted = self.conjunctionSplitter.split(baseString)
        # regroup, so tokens in parenthesis are joined
        groups = []
        str = ""
        for i in range(0,len(splitted)):
            str += " "+splitted[i]
            if str.count("(") == str.count(")"):
                str = str.strip();
                if str[0] == "(":
                    str = str[1:-1]
                groups.append(str)
                str = ""
        if str != "":
            raise ("Unmatched parenthesis in group %s " % str)
       
        
        return groups
    
    def _get_expression(self,exp):
        splitted = self.operatorSplitter.split(exp)
        
        if len(splitted) != 3:
            raise "Invalid expression %s " % exp

        return (splitted[0],splitted[1],splitted[2])
        
        

