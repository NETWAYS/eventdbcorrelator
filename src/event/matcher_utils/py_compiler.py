import logging
from constants import *


'''
Compiler that compiles a MatcherTree instance directly to python code 

'''
class PyCompiler(object):
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
            return "self.regexp_test(%s,%s) " % (value,field)
        
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
        