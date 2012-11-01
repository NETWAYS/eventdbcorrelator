

Developing EDBC
===============

Writing processors
------------------

Processors can be easily written and  added to edbc, here is a short guide:

#. add a new processor file to the lib/processor package and give it the name %type%_processor.py (where type is the name of your processor). define a class called %type%Processor (where type starts with a capital letter). You can use the NullProcessor as an template here.
 
#. Setup your clas:
        * Define a setup(self,id,config={}) method. 'id' will be the id defined in the component configuration (the one in the brackets) and config will be a dict of the key=value definitions that are set in the compontents configuration. You're free to setup your processor here
        * Define a process(self,event) method. This will be called with the event when the chain containing your custom processor is executed. You can do anything you want with the event. 
        * Add your file to the __init__.py of the processor package 


.. note:: If you're writing a lot to the database, use the execute_after_flush method of the datasource.
