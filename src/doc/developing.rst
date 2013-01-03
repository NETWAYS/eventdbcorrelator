
***************
Developing EDBC
***************

Running the testcases
---------------------

In order to run the testcases, you have to create an empty database and a testuser::

    CREATE USER testcases@localhost IDENTIFIED BY 'testcases';
    CREATE DATABASE test_eventdb;
    GRANT ALL PRIVILEGES ON test_eventdb.* TO testcases@localhost;

You can now run the tests either by calling ./runtests.py underneath the lib folder or by using nosetest::

    cd {YOUR BUILD PATH}/lib
    nosetests --with-xunit

.. note:: If you want to use other settings, adjust the SETUP_DB and SETUP_DB_FLUSHING dictionaries underneath tests/mysql_datasource_test.py


Writing processors
------------------

Processors can be easily written and  added to edbc, here is a short guide:

#. add a new processor file to the lib/processor package and give it the name %type%_processor.py (where type is the name of your processor). define a class called %type%Processor (where type starts with a capital letter). You can use the NullProcessor as an template here.
 
#. Setup your class:
        * Define a setup(self,id,config={}) method. 'id' will be the id defined in the component configuration (the one in the brackets) and config will be a dict of the key=value definitions that are set in the compontents configuration. You're free to setup your processor here
        * Define a process(self,event) method. This will be called with the event when the chain containing your custom processor is executed. You can do anything you want with the event. 
        * Add your file to the __init__.py of the processor package 


.. note:: If you're writing a lot to the database, use the execute_after_flush method of the datasource. This delays the actual query write for a few ms and executes all queries that
          were submitted during this time in one transaction.

