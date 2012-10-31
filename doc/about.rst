.. _about_label:

What is EDBC?
=============

EDBC (EventDB Correlator) is an agent for `EventDB <https://www.netways.org/projects/eventdb/wiki>`, our tool for integrating passive monitoring (like snmp, syslog or mail events) into icinga (or similar) monioring enviromnents. 
EDBC offers a lot of features that are required to cover advanced monitoring use cases:

* Pipe based event collection with the possibility to define your own input formats 
* Basic support for acting as a snmp_agent by parsing and using SNMPTT mib files
* Aggregation of events based on advanced matcher patterns 
* Clearance of aggregations via clear matchers or by timeout
* Extensible and easy to understand event processor mechanismn for writing your own processors



