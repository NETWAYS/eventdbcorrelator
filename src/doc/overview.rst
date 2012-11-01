

Overview
========

This section provides a few information about how edbc is structured and a short overview of the configuration. Configuration topics are discussed in depth in :ref:Configuration. 


File layout
-----------

- **bin/**: Contains the edbc binary, which just calls lib/edbc.py
- **lib/**: Contains the source code 
- **libexec/**: Contains executable templates, for example the snmp_handler 
- **etc/**: Configuration and chain files are defined here 

Configuration files
-------------------

There are two types of configuration files: \*.cfg files and ^*.chain files 

.cfg files
``````````
\*.cfg can be found underneath etc/conf.d (or another path if you modify your edbc.cfg file's *configdir* directive. In this documentation we assume that configurations are under etc/conf.d) and define resources the chains can work with. These files are in the `ConfigParser Format <http://docs.python.org/2/library/configparser.html>`_ and therefore rather simple:

- \[Brackets\] define identifiers. These can later be referenced with @, but this will be discussed in :ref:`Configuration`
- Values for components are just defined using a "Key: Value" Syntax  

.chain files
````````````
Chain files define how your event will processed and consist at least of one 'in' value and one 'to_{nr}' value. the {nr} defines at which position a processer stands. See :ref:`Configuration` for more details.

Important files
```````````````
- **etc/edbc.cfg** contains the 'global' section and defines, in which directories 
- In a default setup, **etc/conf.d/database.cfg** contains the database credentials.
- **etc/conf.d/base_processors.cfg** contains a few processors and examples for some use cases

 
