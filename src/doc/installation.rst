
************
Installation
************

Prerequisites
=============

You only need a minimal python setup in order to use edbc:

* Python 2.4+ (no Python 3 support)
* MySQLdb


.. _configure-label:

Installing the executables 
==========================


EDBC can be installed via make::

	./configure --with-db-user=eventdb --with-db-pass=%YOUR DB PASSWORD&
	make

This installs EDBC under /usr/local/edbc. If you prefer a different path, use 
the --prefix option in configure.

.. note:: For additional configuration options, call ./configure --help.


Setting up the database
=======================

Currently, only MySQL is supported. You can find the .sql schema files under etc/schema. call::
	
	mysql -u root -p
	mysql> CREATE DATABASE eventdb;
	mysql> CREATE USER eventdb IDENTIFIED BY '%YOUR PASSWORD%';
	mysql> GRANT SELECT, INSERT, UPDATE, DELETE ON eventdb.* TO eventdb;
	mysql> FLUSH PRIVILEGES;
	mysql> quit;

	cd etc/schema/mysql
	mysql -u root -p eventdb < mysql_create.sql

Your password should be the one defined in your configure call (see :ref:`configure-label`).

.. note:: If you change your database credentials afterwards, you can modify the etc/conf.d/database.cfg in your installation path.


