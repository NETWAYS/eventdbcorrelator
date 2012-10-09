
class DBTransformer(object):
    
    def transform(self,event):
        if event["source"] == "snmp":
            return self.transform_snmp(event)
        if event["source"] == "syslog":
            return self.transform_syslog(event)
        
    
    def transform_snmp(self,event):
        return {
            "host_name" : event["host_name"],
            "host_address" : event["host_address"].bytes,
            "type" : 1,
            "facility" : 1,
            "priority" : 1,
            "program" : event["program"],
            "message" : event["message"],
            "ack"     : event["ack"],
            "created" : event["created"],
            "modified": event["modified"]
        }

    def transform_syslog(self,event):
        return {
            "host_name" : event["host_name"],
            "host_address" : event["host_address"].bytes,
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