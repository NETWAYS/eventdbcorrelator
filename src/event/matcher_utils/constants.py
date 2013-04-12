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
CONJUNCTIONS = ["AND","OR","AND NOT","OR NOT"]
EXPRESSION_STRING_OPERATORS = ['IS NOT','CONTAINS','REGEXP','DOES NOT CONTAIN','STARTS WITH','ENDS WITH','IS']
EXPRESSION_ATTRIBUTE_OPERATORS = ['ATTRIBUTE']
EXPRESSION_SET_OPERATORS = ['NOT IN','IN']
EXPRESSION_IP_OPERATORS = ['IN IP RANGE','NOT IN IP RANGE','NOT IN NETWORK','IN NETWORK']
EXPRESSION_NUMERIC_OPERATORS = ['>=','<=','>','!=','<','=']

EXPRESSION_OPERATORS = EXPRESSION_IP_OPERATORS+EXPRESSION_ATTRIBUTE_OPERATORS+EXPRESSION_STRING_OPERATORS+EXPRESSION_NUMERIC_OPERATORS+EXPRESSION_SET_OPERATORS
