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
from matcher_utils import MatcherTree, PyCompiler

class TrueMatcher(object):
    """ Matcher that always returns true. Use this when you implement an optional
        matcher parameter and want to allow users to use no matcher definition

    """


    def get_match_groups(self):
        """ No matching, no groups, so this returns an empty dict
        """
        return {}
    
    def matches(self, event):
        """ returns True
        """
        return True


class FalseMatcher(object):
    """ Matcher that always returns false.

    """


    def get_match_groups(self):
        """ no matching, no groups. so this returns an empty dict

        """
        return {}
    
    def matches(self, event):
        """ returns True
        """
        return False
 
        
class Matcher(object):
    """ Matchers take objects (in our case evens) and match them with a query string. In this case
        MatcherTree takes the string and builds a binary tree out of the definition, which is then compiled
        by the PyCompiler to an python lambda expression - so this should be rather fast in runtime.

    """


    def __init__(self, definition):
        self.string_tokens = {}
        self.originalString = definition
        self.working_string = definition
        
        self.string_finder = re.compile('[^\\\]{0,1}(\'.+?\'|".+?")[^\\\]{0,1}', re.IGNORECASE)
        self._parse_definition()

    def _parse_definition(self):
        """ Creates a MatcherTree from the string expression and compiles it via the PyCompiler
            to python code

        """
        self._tokenize_strings()
        self.tree = MatcherTree(self.working_string, self.string_tokens)
        self.tree.compile(PyCompiler(self.string_tokens))
        
    def _tokenize_strings(self):
        """ Takes the expression and substitues all strings with #TOKEN{0}, #TOKEN{1}, etc.
            the tokens are stored in the internal stringTokens list and are converted to the actual strings
            in the MatcherTree. This prevents string expressions from being interpreted as operators and allows us
            to use a regular expression instead of a state machine approach when parsing the expression.

        """
        match = self.string_finder.findall(self.working_string)
        token_nr = 0
        for string in match:
            token = "#TOKEN{%i}" % token_nr
            self.string_tokens[token] = string
            self.working_string = self.working_string.replace(string, token)
            token_nr += 1
    
    def __getitem__(self,group_id):
        """ returns the group stored currently. Not threadsafe!

        """
        if group_id in self.tree.regex_groups:
            return self.tree.regex_groups[group_id]
        return None
    
    def get_match_groups(self):
        """ Returns the matchgroups of the last match. Neither threadsafe nor reentrant, so make sure to lock
            correctly when using it.

        """
        return self.tree.regex_groups

    def matches(self, event):
        """ Returns true when event matches this expression, otherwise false. Regular expression groups can afterwards
            be retrieved with get_match_groups()

        """
        return self.tree.test(event)
        

