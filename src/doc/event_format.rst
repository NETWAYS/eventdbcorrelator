
.. _event_format:

**************
EventDB Events
**************

Events in the eventdb have the following properties that will be persisted in the database and can be set by :ref:`transformer-ref` or :ref:`processor-ref`:

* message : The message displayed for standalone events
* host: The name of the host the event is associated with as a string
* host_address: The IP address of the event (IPv4 or IPv6)
* facility: The facility of the event as a number (see `RFC 5424 <http://tools.ietf.org/html/rfc5424#section-6.2.1>`_)
* priority: The priority of the event as a number
* program: The program that triggered the event
* type: The type of the event (default: syslog or snmp)
* ack: 0 if the event is not acknowledged, else 1
* created: The date of the events creation
* modified: The date of the last event modification (which is, for example, that a new event was added to an aggregation group)


