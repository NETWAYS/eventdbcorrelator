CONJUNCTIONS = ["AND","OR","AND NOT","OR NOT"]
EXPRESSION_STRING_OPERATORS = ['IS NOT','CONTAINS','REGEXP','DOES NOT CONTAIN','STARTS WITH','ENDS WITH','IS']
EXPRESSION_ATTRIBUTE_OPERATORS = ['ATTRIBUTE']
EXPRESSION_SET_OPERATORS = ['NOT IN','IN']
EXPRESSION_IP_OPERATORS = ['IN IP RANGE','NOT IN IP RANGE','NOT IN NETWORK','IN NETWORK']
EXPRESSION_NUMERIC_OPERATORS = ['>=','<=','>','!=','<','=']

EXPRESSION_OPERATORS = EXPRESSION_IP_OPERATORS+EXPRESSION_ATTRIBUTE_OPERATORS+EXPRESSION_STRING_OPERATORS+EXPRESSION_NUMERIC_OPERATORS+EXPRESSION_SET_OPERATORS