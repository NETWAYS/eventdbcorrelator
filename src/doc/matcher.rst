.. _matcher-syn:

*******************
EDBC Matcher syntax
*******************

Syntax definition
-----------------

The syntax for matchers can be::

	MATCHER: MATCHER_STMT | MATCHER CONJUNCTION MATCHER_STMT  | (MATCHER)
	
	MATCHER_STMT: STRING_MATCHER | NUMERIC_MATCHER | SET_MATCHER | IP_MATCHER 
	STRING_MATCHER: #field STRING_OPERATOR STRING
	NUMERIC_MATCHER: #field NUMERIC_OPERATOR #NUMBER
	SET_MATCHER: #field SET_OPERATOR (SET) 
	IP_MATCHER: #field IP_OPERATOR_DEFINITION 
        
	STRING_OPERATOR: ['IS NOT','CONTAINS','REGEXP','DOES NOT CONTAIN','STARTS WITH','ENDS WITH','IS']
 	SET_OPERATOR:	 ['NOT IN','IN']
	NUMERIC_OPERATOR:['>=','<=','>','!=','<','=']

	IP_OPERATOR_DEFINITION: IN IP RANGE '#ip "-" #ip' | NOT IN IP RANGE '#ip "-" #ip' | IN NETWORK '#submask_or_cidr'| NOT IN NETWORK '#submask_or_cidr'
	SET = #value | SET, #value
	CONJUNCTION: ["OR","AND", CONJUNCTION " NOT" ]


Examples
---------

#. **Simple message check**::
	
	message IS 'message to check'

#. **Simple message check with priority**::

	message IS 'message to check' AND priority >= 4

#. **REGEXP check**::

	message REGEXP 'srv-[A-Za-z]\d+' 

#. **Limit to network**::
	
	host_address IN NETWORK "192.168.0.0/24"

#.  **Limit to ip range**::
	
	host_address IN IP RANGE "192.168.4.4-192.168.5.2"


Pitfalls
---------

* Operators and conjunctions **must** be uppercase in matchers
* Regexp and String matchers are case insensitive
* The only string operators supported on host_address are =, use the ip operators for advanced checks here


