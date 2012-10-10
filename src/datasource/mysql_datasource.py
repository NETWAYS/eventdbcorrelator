
import MySQLdb
import Queue
import threading
import db_transformer
import time
from event import *

LOCATION_SETUP_SCHEME = "./database/mysql_create.sql"
LOCATION_TEARDOWN_SCHEME="./database/mysql_teardown.sql"

class MysqlGroupCache(object):
    def __init__(self):
        self.lock = threading.Lock() 
        self.groups = {}
        
    def add(self,group):
        self.groups[group["group_id"]] = group
        group["dirty"] = False
        if not "group_active" in group:
            group["group_active"] = 1
        if not "modified" in group:
            self.update_time(group["group_id"])
        
        
    def clear(self,group_id):
        try:
            self.lock.acquire()
            if group_id in self.groups: 
                del self.groups[group_id] 
        finally:
            self.lock.release()
    
    def update_time(self,groupId):
        self.lock.acquire()
        try:
            if not groupId in self.groups:
                return
            
            self.groups[groupId]["modified"] = time.localtime()
            self.groups[groupId]["dirty"] = True
        finally:
            self.lock.release()
    
    def deactivate(self,groupId):
        
        self.lock.acquire()
        try:
            if not groupId in self.groups:
                return

            self.groups[groupId]["group_active"] = 0
            self.groups[groupId]["dirty"] = True
        finally:
            self.lock.release()
        
    def get(self,groupId):
        try:
            self.lock.acquire()

            if groupId in self.groups and self.groups[groupId]["group_active"] == 1:
                return self.groups[groupId]
            return None
        finally:
            self.lock.release()
        
    def flush_to_db(self,conn,table):
        try:
            cursor = conn.cursor()
            self.lock.acquire()
            for groupId in self.groups:
                group = self.groups[groupId]
                if not group["dirty"]:
                    continue
                group["modified_ts"] = time.mktime(group["modified"])
                cursor.execute("UPDATE "+table+" SET group_active=%(group_active)s, modified=FROM_UNIXTIME(%(modified_ts)s) WHERE id=%(group_leader)s",group)
                group["dirty"] = False
                if not group["group_active"]:
                    self.clear(groupId)
        finally:
            self.lock.release()
            cursor.close()
            conn.commit()
        
class MysqlDatasource(object):
    
    
    def setup(self,id,config):
        self.id = id
        self.host = config["host"]
        self.port = config["port"]
        self.user = config["user"]
        self.password = config["password"]
        self.database = config["database"]

        if "spool" in config:
            self.spool = config["spool"]
        else:
            self.spool = None
        
        if "poolsize" in config:
            self.poolsize = config["poolsize"]
        else:
            self.poolsize = 10
            
        if "table" in config:
            self.table = config["table"]
        else:
            self.table = "event"
        if "transform" in config:
            self.out = config["transform"]
        else:
            self.out = db_transformer.DBTransformer()
        
        self.available_connections = []
        self.connections = Queue.Queue()
        self.lock = threading.Lock()
        self.connect()
        try:
            
            self.fetch_active_groups()
            self.fetch_last_id()
            
        except:
            pass


    def connect(self):
        if not self.connections.empty():
            return
        
        for i in range(0,self.poolsize):
            c = self.get_new_connection()
            if c :
                self.connections.put(c)
                self.available_connections.append(c)

        
        
    def fetch_active_groups(self):
        self.group_cache = MysqlGroupCache()
        groups = self.execute("SELECT group_active,id,group_id,modified FROM "+self.table+"  WHERE group_active = 1 AND group_leader = -1");

        for group in groups:
            
            groupDesc = {
                "group_active" : group[0],
                "group_leader" : group[1],
                "group_id" : group[2],
                "modified": group[3].timetuple()
            }
            self.group_cache.add(groupDesc)
        
        
        
    def test_setup_db(self):
        sql_file = open(LOCATION_SETUP_SCHEME,'r')
        setup_sql = ""
        for line in sql_file:
            setup_sql += "%s" % line
        self.execute(setup_sql)
        self.fetch_active_groups()
        self.fetch_last_id()

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
        return True
    
    def insert(self,event):
        
        conn = self.acquire_connection()
        try: 
            cursor = conn.cursor()

            query = "INSERT INTO "+self.table+" (id, host_name,host_address,type,facility,priority,program,message,alternative_message,ack,created,modified,group_active,group_id,group_leader) VALUES (%(id)s,%(host_name)s,%(host_address)s,%(type)s,%(facility)s,%(priority)s,%(program)s,%(message)s,%(alternative_message)s,%(ack)s,NOW(),NOW(),%(group_active)s,%(group_id)s,%(group_leader)s);"
            
            self.execute(query,self.get_event_params(event),noResult=True,cursor=cursor)
            
            if event.group_leader and event.group_leader > -1:
                self.update_group_modtime(event.group_id)
            else:
                self.group_cache.add({
                    "active" : 1,
                    "group_leader" : event["id"],
                    "group_id" : event.group_id,
                    "dirty" : True
                });
            cursor.close()
            conn.commit()
            return event["id"]
        finally:
            self.release_connection(conn)
    
    
    def get_event_params(self,event):
        event["id"] = self.next_id()
        
        params = self.out.transform(event)
        params["id"] = event["id"]
        params["group_leader"] = event.group_leader
        params["group_id"] = event.group_id
        params["alternative_message"] = event.alternative_message
        params["group_active"] = int(event.in_active_group())
        
        return params
    
    
    def update_group_modtime(self,group_id):
        self.group_cache.update_time(group_id)
    
    
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
        conn = None
        try:
            if not cursor_given:
                conn = self.acquire_connection()
                cursor = conn.cursor()
            
            cursor.execute(query,args)
            if not noResult:
                result = cursor.fetchall()
                return result
            
            return ()
        finally:
            
            if cursor != None and not cursor_given:
                cursor.close()
            if conn:
                conn.commit()
                self.release_connection(conn)
                
                
    def get_event_by_id(self,event_id):	
        eventfields = ("id","host_name","host_address","type","facility","priority","program","message","alternative_message","ack","created","modified","group_id","group_leader","group_active")
        event = self.execute("SELECT %s FROM event WHERE id = %i AND active = 1 " % (",".join(eventfields),int(event_id)))
        if len(event) < 1:
            return None
        return Event(record={"data": event[0],"keys":eventfields})
        
    
    def get_group_leader(self,group_id):
        group = self.group_cache.get(group_id)
        
        if not group:
            return (None,None)
        return (group["group_leader"],time.mktime(group["modified"]))
    
    
    def deactivate_group(self,groupId):
        self.group_cache.deactivate(groupId)
        
    
    def close(self,noFlush=False):
        try:
            conn = self.acquire_connection()
            if not noFlush:
                self.group_cache.flush_to_db(conn,self.table)
        finally:
            conn.close()
            
    def execute_spooled(self,c):
        if not self.spool:
            return
        ctr = 0
        for i in self.spool.get_spooled():
            ctr = ctr+1
            c.execute(i[0],i[1])
        logging.debug("Insert %i events from spool" % ctr)
    def get_new_connection(self):
        try:
            c = MySQLdb.Connection(
                host=self.host,
                port=int(self.port),
                user=self.user,
                passwd=self.password,
                db=self.database
            )
            try:
                self.execute_spooled(c)
            except e:
                pass
                
            return c
        except MySQLdb.OperationalError,oe:
            logging.error(oe)
            return
            
   
    def fetch_last_id(self):
        res = self.execute("SELECT id FROM event ORDER BY id LIMIT 1")
        if len(res) < 1:
            self.last_id = 0
            return
        self.last_id = res[0][0]
    
    def next_id(self):
        try:
            self.lock.acquire()
            self.last_id = self.last_id+1
            return self.last_id
        finally:
            self.lock.release()
            
    def acquire_connection(self):
        try:
            conn = self.connections.get(True,3)
            if not conn.open:
                conn = self.get_new_connection()
            return conn
        except Queue.Empty, e:
            if self.spool:
                return self.spool
            else:
                return None
        
    
    def release_connection(self,conn):
        if not conn.open:
            conn = self.get_new_connection()
        self.connections.put(conn)