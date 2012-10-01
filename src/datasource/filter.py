# To change this template, choose Tools | Templates
# and open the template in the editor.
import re
import logging 

class FilterGroup(object):
    def __init__(self,type="AND",items = []):
        self.items = items
        self.type = type
   
    def add(self,filter):
        if getattr(filter,"__iter__",False):
            self.items = self.items + filter
        else:
            self.items.append(filter)
        
    def matches(self,event):
        for item in self.items:
            matches = item.matches(event)
            if matches == True and self.type == "OR":
                return True
            if matches == False and self.type == "AND":
                return False
        if self.type == "OR": # no match for every item
            return False
        if self.type == "AND": # every item matched
            return True
        
    def toSQL(self):
        sql = "("
        first = True
        for item in self.items:
            if first == False:
                sql += " "+self.type+" "
            sql += item.toSQL()
            first = False
        return sql + ")"

class Filter(object):
    def __init__(self,field,operator,value):
       
        self.field = field
        self.operator = operator
        if self.operator == "IN":
            self.value = value.split(",")
        else: 
            if self.operator == "MATCH":
                self.value = re.compile(value)
            else:
                self.value = value
    
    def matches(self,event):
        if self.operator == "IS":
            return event[self.field] == self.value
        if self.operator == "MATCH":
            return self.value.search(event[self.field]) != None
        if self.operator == ">":
            return event[self.field] > self.value
        if self.operator == "<":
            return event[self.field] < self.value
        if self.operator == "IN":
            for value in self.value:
                if event[self.field] == value:
                    return True
            return False
        
    
    def toSQL(self):
        value = self.value
        operator = self.operator
        if operator == "IS":
            operator = "="
        if operator == "MATCH":
            operator = "REGEXP"
            value = value.pattern
        if self.operator == "IN":
            value = "('"+("','".join(value))+"')"
        return "%s %s '%s'" % (self.field,operator,value)