
import re
import logging 


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
        self.tree.compile()
        
        
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
EXPRESSION_NUMERIC_OPERATORS = ['>=','<=','>','!=','<','=']

EXPRESSION_OPERATORS = EXPRESSION_STRING_OPERATORS+EXPRESSION_NUMERIC_OPERATORS+EXPRESSION_SET_OPERATORS


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
        self.conjunctionSplitter = re.compile("("+"|".join(CONJUNCTIONS)+")",re.IGNORECASE)
        self.operatorSplitter = re.compile("("+"|".join(EXPRESSION_OPERATORS)+")",re.IGNORECASE)
    
    
    def is_expression(self,node):
        return node["root"] in EXPRESSION_OPERATORS
    
    def is_conjunction(self,node):
        return node["root"] in CONJUNCTIONS
    
    def _compile_expression(self,node):
        if node["root"] in EXPRESSION_STRING_OPERATORS:
            node["compiled"] = self._compile_string_expression(node)
        if node["root"] in EXPRESSION_NUMERIC_OPERATORS:
            node["compiled"] = self._compile_numeric_expression(node)
        if node["root"] in EXPRESSION_SET_OPERATORS:
            node["compiled"] = self._compile_set_expression(node)
        return node
    
    def _compile_string_expression(self,node):
        value = ""
        if node["right"] in self.tokens:
            value = self.tokens[node["right"]].lower()
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
            return "re.search(%s,%s) != None" % (value,field)
        
        return "False"
    
        
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
        
    
    def compile(self):
        self.traverse(self.is_expression,self._compile_expression)
        self.traverse(self.is_conjunction,self._build_python_expression,self.rawTree,True)
        self.compiledMatcher = lambda event : eval(self.rawTree["compiled"])

    def test(self,event):
        if self.compiledMatcher == None:
            self.compile()
        try :
            return self.compiledMatcher(event)
        except AttributeError:
            return False

    def _build_python_expression(self,node):
        node["compiled"] = "%s %s %s" % (node["left"]["compiled"],node["root"].lower(),node["right"]["compiled"])
        return node

        
    def traverse(self,matcherFn=lambda tnode:True,handler=lambda tnode:tnode,node=None,bottomUp=False):
        if node == None:
            node = self.rawTree
        
        # Bottom up parsing
        if self.is_conjunction(node) and bottomUp:
            self.traverse(matcherFn,handler,node["left"])
            self.traverse(matcherFn,handler,node["right"])
        
        if matcherFn(node):
            node = handler(node)
        
        # Top down parsing
        if self.is_conjunction(node) and not bottomUp:
            self.traverse(matcherFn,handler,node["left"])
            self.traverse(matcherFn,handler,node["right"])

    

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
            groups[2] = " ".join(groups[2:])
        return {
            "root" : groups[1].upper(),
            "left" : self._get_query_node(groups[0]),
            "right": self._get_query_node(groups[2])
        }

    def _get_conjunction_groups(self,baseString):
        splitted = self.conjunctionSplitter.split(baseString)
        # regroup, so tokens in parenthesis are joined
        groups = []
        str = ""
        for i in range(0,len(splitted)):
            str += splitted[i]
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
        
        

