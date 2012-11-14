
class DBTransformer(object):
    
    def transform(self,event):
        if event["source"] == "snmp":
            return self.transform_snmp(event)
        if event["source"] == "syslog":
            return self.transform_syslog(event)
        if event["type"]:
            return self.transform_syslog(event,event["type"])
    
    def transform_snmp(self,event):
        return {
            "host_name" : event["host_name"],
            "host_address" : event["host_address"].bytes,
            "type" : 1,
            "facility" : 1,
            "priority" : event["priority"],
            "program" : event["program"],
            "message" : event["message"],
            "ack"     : event["ack"],
            "created" : event["created"],
            "modified": event["modified"]
        }

    def transform_syslog(self,event,nr=0):
        return {
            "host_name" : event["host_name"],
            "host_address" : event["host_address"].bytes,
            "type" : nr,
            "facility" : event["facility"],
            "priority" : event["priority"],
            "program" : event["program"],
            "message" : event["message"],
            "ack"     : event["ack"],
            "created" : event["created"],
            "modified": event["modified"]
        }
        
    def transform_mail(self,event):
        pass
