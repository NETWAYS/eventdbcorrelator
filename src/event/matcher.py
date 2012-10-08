
import re
import logging 
import socket
import ip_address

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
        self.tree.compile(PythonMatcherCompiler(self.stringTokens))
        
        
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
    


CONJUNCTIONS = ["AND","OR","AND NOT","OR NOT"]
EXPRESSION_STRING_OPERATORS = ['IS NOT','CONTAINS','REGEXP','DOES NOT CONTAIN','STARTS WITH','ENDS WITH','IS']
EXPRESSION_SET_OPERATORS = ['NOT IN','IN']
EXPRESSION_IP_OPERATORS = ['IN IP RANGE','NOT IN IP RANGE','NOT IN NETWORK','IN NETWORK']
EXPRESSION_NUMERIC_OPERATORS = ['>=','<=','>','!=','<','=']
EXPRESSION_OPERATORS = EXPRESSION_IP_OPERATORS+EXPRESSION_STRING_OPERATORS+EXPRESSION_NUMERIC_OPERATORS+EXPRESSION_SET_OPERATORS

class PythonMatcherCompiler(object):
    def __init__(self,tokens):
        self.tokens = tokens
        self.COMPILE_ATTR = "compiled_py"
        
    def compile_expression(self,node):
        if node["root"] in EXPRESSION_STRING_OPERATORS:
            node[self.COMPILE_ATTR] = self._compile_string_expression(node)
        if node["root"] in EXPRESSION_NUMERIC_OPERATORS:
            node[self.COMPILE_ATTR] = self._compile_numeric_expression(node)
        if node["root"] in EXPRESSION_SET_OPERATORS:
            node[self.COMPILE_ATTR] = self._compile_set_expression(node)
        if node["root"] in EXPRESSION_IP_OPERATORS:
            node[self.COMPILE_ATTR] = self._compile_network_expression(node)
        if not self.COMPILE_ATTR in node:
            node[self.COMPILE_ATTR] = " False "
        return node
    
    def _compile_string_expression(self,node):
        value = ""
        if node["right"] in self.tokens:
            value = self.tokens[node["right"]]
            if not node["root"] == "REGEXP":
                value = value.lower()
        else:
            value = "event[\"%s\"].lower()" % node["right"]
        field = "event[\"%s\"].lower()" % node["left"]
        
        operator = node["root"]

        if(operator in ["IS","IS NOT"]):
            return "%s %s %s" % (field,{"IS":"==","IS NOT": "!="}[operator],value)
        
        if operator in ["CONTAINS","DOES NOT CONTAIN"]:
            return "%s.find(%s) %s -1" (field,value,{"CONTAINS":">","DOES NOT CONTAIN":"=="})
        if operator  == "STARTS WITH":
            return "%s.startswith(%s)" % (field,value)
        if operator == "ENDS WITH":
            return "%s.endswith(%s)" % (field,value)
        if operator == "REGEXP":
            return "re.search(%s,%s,re.IGNORECASE) != None" % (value,field)
        
        return "False" 
    
    def _compile_network_expression(self,node):
        value = ""
        if node["right"] in self.tokens:
            value = self.tokens[node["right"]]
            if not node["root"] == "REGEXP":
                value = value.lower()
        else:
            value = "event[\"%s\"].lower()" % node["right"]
        field = "event[\"%s\"].lower()" % node["left"]
        
        operator = node["root"]
        if operator in ["IN NETWORK","NOT IN NETWORK"]:
            if operator.startswith("NOT"):
                expected = "False"
            else:
                expected = "True"
            return "ip_address.IPAddress(%s).in_network(%s) == %s " % (field,value,expected)
            
        
        if operator in ["IN IP RANGE","NOT IN IP RANGE"]:
            if operator.startswith("NOT"):
                expected = "False"
            else:
                expected = "True"
            value = value.split("-")
            
            return "ip_address.IPAddress(%s).in_range('%s','%s') == %s " % (field,value[0].strip("'\""),value[1].strip("'\""),expected)
            
        return False
        
    def _compile_numeric_expression(self,node):
        value = ""
        try:
            value = float(node["right"])
        except ValueError:
            value = "event[\"%s\"]" % node["right"]
        
        field = "event[\"%s\"]" % node["left"]
        operator = node["root"]
        if operator == "=":
            operator = "=="
        return "%s %s %s" % (field, operator, value)
        
    
    def _compile_set_expression(self,node):
        value = node["right"]
        value = value.strip("()").split(",")
        
        convertedValues = []
        for token in value:
            if token in self.tokens:
                token = self.tokens[token]
            else:
                try:
                    token = float(token)
                    if int(token) == token:
                        token = int(token)
                    token = str(token)
                except ValueError:
                    token = "event[\"%s\"]" % token
                
            convertedValues.append(token)
        
        value = "["+",".join(convertedValues)+"]"
        operator = node["root"]
        field = "event[\"%s\"]" % node["left"]
        
        return "%s %s %s" % (field, operator.lower(), value)
    
    def build_expressions(self,node):
        try:
            node[self.COMPILE_ATTR] = "%s %s %s" % (node["left"][self.COMPILE_ATTR],node["root"].lower(),node["right"][self.COMPILE_ATTR])
        except KeyError,e:
            logging.error("Could not compile node %s" % node)
            node[self.COMPILE_ATTR] = "False"
        return node
        
    
class MatcherTree(object):
    
    def __init__(self,queryString,tokens):
        self.tokens = tokens
        self._prepare_regexp()
        self.rawTree = self._get_query_node(queryString)
        self.compiled = ""
        self.precompiled_regexp = {}
        self.regex_counter = 0
        self.compiledMatcher = None
        
        
    def _prepare_regexp(self):
        self.conjunctionSplitter = re.compile(" ("+"|".join(CONJUNCTIONS)+") ",re.IGNORECASE)
        self.operatorSplitter = re.compile(" ("+"|".join(EXPRESSION_OPERATORS)+") ",re.IGNORECASE)
    
    
    def is_expression(self,node):
        return node["root"] in EXPRESSION_OPERATORS
    
    def is_conjunction(self,node):
        return node["root"].strip() in CONJUNCTIONS
    
    
    def compile(self,compiler):
        self.traverse(self.is_expression,compiler.compile_expression)
        self.traverse(self.is_conjunction,compiler.build_expressions,self.rawTree,True)
        self.compiledMatcher = lambda event : eval(self.rawTree[compiler.COMPILE_ATTR])

    def test(self,event):
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
        
        

