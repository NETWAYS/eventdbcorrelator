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
import logging
from constants import *



class PyCompiler(object):
    """ Compiles MatcherTree instances to a python lambda expression
        Trees

    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.COMPILE_ATTR = "compiled_py"
        
    def compile_expression(self, node):
        """ Compiles an expression (LVALUE OPERATOR RVALUE) and returns the compiled node part

        """
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
    
    

    def _compile_string_expression(self, node):
        """ Compiles a string expression and returns it as a string containing the
            python code

        """

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
            return "%s %s %s" % (field,{"IS":"==","IS NOT": "!="}[operator], value)
        
        if operator in ["CONTAINS","DOES NOT CONTAIN"]:
            return "%s.find(%s) %s -1" % (field, value, {"CONTAINS" : ">", "DOES NOT CONTAIN" : "==" }[operator])
        if operator  == "STARTS WITH":
            return "%s.startswith(%s)" % (field, value)
        if operator == "ENDS WITH":
            return "%s.endswith(%s)" % (field, value)
        if operator == "REGEXP":
            return "self.regexp_test(%s,%s) " % (value, field)
        
        return "False" 
    
    def _compile_network_expression(self, node):
        """ Compiler for network expressions like IN NETWORK, IN IP RANGE, etc.

        """

        value = ""
        if node["right"] in self.tokens:
            value = self.tokens[node["right"]]
            if not node["root"] == "REGEXP":
                value = value.lower()
        else:
            value = "event[\"%s\"].lower()" % node["right"]
        field = "event[\"%s\"].lower()" % node["left"]
        
        operator = node["root"]
        if operator in ["IN NETWORK", "NOT IN NETWORK"]:
            if operator.startswith("NOT"):
                expected = "False"
            else:
                expected = "True"
            return "ip_address.IPAddress(%s).in_network(%s) == %s " % (field, value, expected)
            
        
        if operator in ["IN IP RANGE", "NOT IN IP RANGE"]:
            if operator.startswith("NOT"):
                expected = "False"
            else:
                expected = "True"
            value = value.split("-")
            
            return "ip_address.IPAddress(%s).in_range('%s','%s') == %s " % (field,value[0].strip("'\""), value[1].strip("'\""), expected)
            
        return False
    
    def _compile_numeric_expression(self, node):
        """ Compiler for numeric expressions

        """

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
        
    
    def _compile_set_expression(self, node):
        """ Compiler for sets, i.e. IN (1,2,3,4), etc.

        """

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
    
    def build_expressions(self, node):
        """ Builds the final expression for each branch (left leaf, center, right leaf). See the MatcherTree for
            further explanation

        """
        try:
            node[self.COMPILE_ATTR] = "%s %s %s" % (node["left"][self.COMPILE_ATTR], node["root"].lower(), node["right"][self.COMPILE_ATTR])
        except KeyError,e:
            logging.error("Could not compile node %s" % node)
            node[self.COMPILE_ATTR] = "False"
        return node
        