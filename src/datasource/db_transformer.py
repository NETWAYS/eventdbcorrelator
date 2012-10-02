'''
  `id` bigint(20) unsigned NOT NULL auto_increment,
  `host_name` varchar(255) NOT NULL,
  `host_address` binary(16) NOT NULL,
  `type` int(11) NOT NULL,
  `facility` int(11) ,
  `priority` int(11) NOT NULL,
  `program` varchar(50) character set ascii NOT NULL,
  `message` varchar(4096) default NULL,
  `ack` tinyint(1) default '0',
  `created` datetime default NULL,
  `modified` datetime default NULL,
'''
class DBTransformer(object):
    
    def transform(self,event):
        return self["transform_%s" % event["source"].lower](event)
    
    def transform_snmp(self,event):
        return {
            "host_name" : event["host_name"],
            "host_address" : event["host_address"],
            "type" : 1,
            "facility" : 1,
            "priority" : 1,
            "program" : event["program"],
            "message" : event["message"],
            "ack"     : event["acked"],
            "created" : event["created"],
            "modified": event["modified"]
        }

    def transform_syslog(self,event):
        return {
            "host_name" : event["host_name"],
            "host_address" : event["host_address"],
            "type" : 0,
            "facility" : event["facility"],
            "priority" : event["priority"],
            "program" : event["program"],
            "message" : event["message"],
            "ack"     : event["acked"],
            "created" : event["created"],
            "modified": event["modified"]
        }
        
    def transform_mail(self,event):
        pass