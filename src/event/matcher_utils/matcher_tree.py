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
import re
from constants import *
from event import ip_address


class MatcherTree(object):
    """ Binary tree that represents a matcher. Nodes are operators or conjunctions, left side
        leafs are fields, right side fields are values. 
        Compiled to python code by the py_compiler.py class. A tree could look like this.

        Expression (HOST_ADDRESS IN NETWORK 10.0.10.0/8 OR PRIORITY >= 4) AND HOST_NAME IS 'string':

                                       AND
                                        |
                               ----------------------------
                               |                          |
                               |                          |
                              OR                          IS
                               |                          |
                  --------------------------        ------------------
                  |                        |        |                |
             IN NETWORK                   >=      HOST_NAME       'string'
                  |                        |
             -----------                -------
             |         |                |     |
    HOST_ADDRESS     10.0.10.0/8    PRIORITY  4

        This tree would be compiled by traversing it in-order (left, root, right) so the result is and adding the
        compiled expression to a 'compiled' field in each branch (but not leafs). The left subtree would be compiled first,
        so it would look like this after the first step

                                       AND
                                        |
                               ------------------------------------------
                               |                                         |
                               |                                         |
                              OR                                         IS
                               |                                         |
                  ------------------------------                    ------------------
                  |                             |                   |                |
COMPILED: IPAdress(event["HOST_ADDRESS"]). event["PRIORITY"] >= 4   HOST_NAME       'string'
                in_network(10.0.10.0/8)


    """
    

    def __init__(self,query_string,tokens):
        self.tokens = tokens
        self._prepare_regexp()
        self.raw_tree = self._get_query_node(query_string)
        self.compiled = ""
        self.regex_groups = {}
        self.compiled_matcher = None
        
    def _prepare_regexp(self):
        """ Precompiles regular expressions for conjuctions and operators.
        
        """
        self.conjunction_splitter = re.compile(" ("+"|".join(CONJUNCTIONS)+") ",re.IGNORECASE)
        self.operator_splitter = re.compile(" ("+"|".join(EXPRESSION_OPERATORS)+") ",re.IGNORECASE)
    
    def is_expression(self,node):
        """ Returns true if node is an expression, false otherwise
            
        """
        return node["root"] in EXPRESSION_OPERATORS
    
    def is_conjunction(self,node):
        """ Returns true if node is a conjunction, false otherwise
        
        """
        return node["root"].strip() in CONJUNCTIONS
    
    def regexp_test(self,reg,val):
        """ regexp_test function that will be called in the compiled python lambda function
            
            SIDE EFFECT: updates self.regex_groups. 
        """
        groups = re.search(reg,val,re.IGNORECASE)
        if not groups:
            return False
        self.regex_groups = dict(self.regex_groups.items() + groups.groupdict().items())
        return True
    
    def compile(self,compiler):
        """ Compiles this tree by the given compiler (which is py_compile in most cases)
            @WARNING: NOT REENTRANT! Lock it and copy hte regex_groups when you use them
            as they might be overwritten by a new run later
        """
        self.traverse(self.is_expression,compiler.compile_expression)
        self.traverse(self.is_conjunction,compiler.build_expressions,self.raw_tree,True)
        self.compiled_matcher = lambda event : eval(self.raw_tree[compiler.COMPILE_ATTR])

    def test(self,event):
        """ Returns true when the event matchs this tree
        """
        self.regex_groups = {}
        if self.compiled_matcher:
            return self.compiled_matcher(event)
        else:
            return False
        
    def traverse(self,matcher_fn=lambda tnode:True,handler=lambda tnode:tnode,node=None,bottom_up=False):
        """ Traverses through the tree  top down or bottom up (if bottom_up is true) starting from root or node and calls 
            handler with the node as a parameter if matcher_fn matches the node

        """
        if node == None:
            node = self.raw_tree
        
        # Bottom up parsing
        if self.is_conjunction(node) and bottom_up:
            self.traverse(matcher_fn,handler,node["left"],bottom_up)
            self.traverse(matcher_fn,handler,node["right"],bottom_up)
        
        if matcher_fn(node):
            node = handler(node)
        
        # Top down parsing
        if self.is_conjunction(node) and not bottom_up:
            self.traverse(matcher_fn,handler,node["left"],bottom_up)
            self.traverse(matcher_fn,handler,node["right"],bottom_up)

    def _get_query_node(self,current_string):
        """ Creates a query node from the string snippet in current_string

        """
        groups = self._get_conjunction_groups(current_string)
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

    def _get_conjunction_groups(self,base_string):
        """ Creates and returns conjunction groups from the string base_string

        """
   
        splitted = self.conjunction_splitter.split(base_string)
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
            raise Exception("Unmatched parenthesis in group %s " % str)
        return groups
    
    def _get_expression(self,exp):
        """ Returns an expression tuple from the string exp (field, operator, value)
        
        """
        splitted = self.operator_splitter.split(exp)
        
        if len(splitted) != 3:
            raise "Invalid expression %s " % exp

        return (splitted[0],splitted[1],splitted[2])
        
        

