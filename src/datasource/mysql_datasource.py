
import MySQLdb
import db_transformer
from event import *

LOCATION_SETUP_SCHEME = "./database/mysql_create.sql"
LOCATION_TEARDOWN_SCHEME="./database/mysql_teardown.sql"

GROUP_NOT_EMPTY_FLAG = 0x1

class MysqlDatasource(object):
    
    
    def setup(self,id,config):
        self.id = id
        self.host = config["host"]
        self.port = config["port"]
        self.user = config["user"]
        self.password = config["password"]
        self.database = config["database"]
        if "table" in config:
            self.table = config["table"]
        else:
            self.table = "event"
        if "transform" in config:
            self.out = config["transform"]
        else:
            self.out = db_transformer.DBTransformer()
        self.connection = False
        self.connect()
        
        
    def connect(self):
        if self.connection and self.connection.open == 1:
            return
                    
        self.connection = MySQLdb.Connection(
            host=self.host,
            port=int(self.port),
            user=self.user,
            passwd=self.password,
            db=self.database
        )
        

    def test_setup_db(self):
        sql_file = open(LOCATION_SETUP_SCHEME,'r')
        setup_sql = ""
        for line in sql_file:
            setup_sql += "%s" % line
        self.execute(setup_sql)
        

    def test_teardown_db(self):
        sql_file = open(LOCATION_TEARDOWN_SCHEME,'r')
        setup_sql = ""
        for line in sql_file:
            setup_sql += "%s" % line
        self.execute(setup_sql)        


    def test_clear_db(self):
        self.test_teardown_db()
        self.test_create_db()


    def is_available(self):
        self.connect()
        return self.connection != None
    
    
    def insert(self,event):
        cursor = self.connection.cursor()
        
        query = "INSERT INTO "+self.table+" (host_name,host_address,type,facility,priority,program,message,alternative_message,ack,created,modified,group_active,group_id,group_leader) VALUES (%(host_name)s,%(host_address)s,%(type)s,%(facility)s,%(priority)s,%(program)s,%(message)s,%(alternative_message)s,%(ack)s,NOW(),NOW(),%(group_active)s,%(group_id)s,%(group_leader)s);"
        
        self.execute(query,self.get_event_params(event),noResult=True,cursor=cursor)
        self.update_event_id(event,cursor)
        if event.group_leader and event.group_leader > -1:
            self.update_group_modtime(event.group_leader)
            
        cursor.close()

        return event["id"]
    
    def get_event_params(self,event):
        params = self.out.transform(event)
        
        params["group_leader"] = event.group_leader
        params["group_id"] = event.group_id
        params["alternative_message"] = event.alternative_message
        params["group_active"] = int(event.in_active_group())
        
        return params
    
    def update_group_modtime(self,leader_id):
        self.execute("UPDATE "+self.table+" SET modified=NOW() WHERE id = %i" % int(leader_id))
    
    def update_event_id(self,event,cursor):
        query = "SELECT LAST_INSERT_ID() FROM "+self.table+";"
        result = self.execute(query,cursor=cursor)
        event["id"] = result[0][0]
    
    def remove(self,event):
        query = "UPDATE %s SET active=0 WHERE id = %i" % (self.table,event["id"])
        self.execute(query)
        
        
    def update(self,event):
        query = "UPDATE "+self.table+" SET host_name=%(host_name)s, host_address=%(host_address)s,type=%(type)s,facility=%(facility)s,priority=%(priority)s,program=%(program)s,message=%(message)s,ack=%(ack)s,created=%(created)s,modified=%(modified)s WHERE id = "+str(event["id"])
        self.execute(query,self.out.transform(event),noResult=True)
        
    
    def execute(self,query,args = (),noResult=False,cursor=None):
        cursor_given = cursor != None
        
        try:
            self.connect()
            if self.connection == None or not self.connection.open:
                return False
            cursor = cursor or self.connection.cursor()
            cursor.execute(query,args)
            if not noResult:
                result = cursor.fetchall()
                return result
            return ()
        finally:
            if cursor != None and not cursor_given:
                cursor.close()
                
    def get_event_by_id(self,event_id):	
        eventfields = ("id","host_name","host_address","type","facility","priority","program","message","alternative_message","ack","created","modified","group_id","group_leader","group_active")
        event = self.execute("SELECT %s FROM event WHERE id = %i AND active = 1 " % (",".join(eventfields),int(event_id)))
        if len(event) < 1:
            return None
        return Event(record={"data": event[0],"keys":eventfields})
        
    
    def get_group_leader(self,group_id):
        query = "SELECT id, UNIX_TIMESTAMP(modified) FROM "+self.table+" WHERE group_id = '%s' AND group_active=1 AND group_leader=-1" % group_id
        result = self.execute(query)

        if len(result) == 0:
            return (None,None)
        logging.debug(result)
        return (result[0][0],result[0][1])
    
    def deactivate_group(self,leaderId):
        self.execute("UPDATE "+self.table+" SET group_active=0 WHERE id=%i" % int(leaderId))
        
    
    def close(self):
        if self.connection != None and self.connection.open == 1:
            self.connection.close()
            
