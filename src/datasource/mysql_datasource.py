
import MySQLdb
import MySQLdb.cursors
import Queue
import traceback
import threading
import db_transformer
import time
from event import *

LOCATION_SETUP_SCHEME = "./database/mysql_create.sql"
LOCATION_TEARDOWN_SCHEME="./database/mysql_teardown.sql"

class MysqlGroupCache(object):
    def __init__(self):
        self.lock = threading.Lock()
        self.deprecated_groups = []
        self.groups = {}
        
    def add(self,group):
        self.groups[group["group_id"]] = group
        group["dirty"] = False
        if not "group_active" in group:
            group["group_active"] = 1
        if not "modified" in group:
            self.add_new_member(group["group_id"])
        
        
    def clear(self,group_id):
        try:
            self.lock.acquire()
            if group_id in self.groups: 
                del self.groups[group_id] 
        finally:
            self.lock.release()
    
    def add_new_member(self,groupId):
        self.lock.acquire()
        try:
            if not groupId in self.groups:
                return
            if not "group_count" in self.groups[groupId]:
                self.groups[groupId]["group_count"] = 0
        
            self.groups[groupId]["group_count"] = self.groups[groupId]["group_count"]+1
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
            self.deprecated_groups.append(self.groups[groupId])
            del self.groups[groupId]
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
       
 
    def flush_deprecated_to_db(self,cursor,table):
        for group in self.deprecated_groups:
            group["modified_ts"] = time.mktime(group["modified"])
            cursor.execute("UPDATE "+table+" SET group_active=%(group_active)s, modified=FROM_UNIXTIME(%(modified_ts)s), group_count=%(group_count)s WHERE id=%(group_leader)s OR group_leader=%(group_leader)s",group)
        self.deprecated_groups = [] 
        

    def flush_to_db(self,conn,table):
        try:
            cursor = conn.cursor()
            self.lock.acquire()
            self.flush_deprecated_to_db(cursor,table)  

            for groupId in self.groups:
                group = self.groups[groupId]
                if not group["dirty"]:
                    continue
                group["modified_ts"] = time.mktime(group["modified"])
                cursor.execute("UPDATE "+table+" SET group_active=%(group_active)s, modified=FROM_UNIXTIME(%(modified_ts)s), group_count=%(group_count)s WHERE id=%(group_leader)s",group)
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

        if "flush_interval" in config:
            self.flush_interval = float(config["flush_interval"])
        else:
            self.flush_interval = 100.0

        if "noFlush" in config:
            self.no_async_flush = True
        else:
            self.no_async_flush = False

        self.flush_pending = False
        self.flush_lock = threading.Lock()
        if "cursor_class" in config:
            self.cursor_class = config["cursor_class"]
        else:
            self.cursor_class = MySQLdb.cursors.Cursor

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
        self.flushlock = threading.Lock()
        self.exec_buffer = []
        self.check_spool = True
        self.connect()
        try:
            self.fetch_active_groups()
            self.fetch_last_id()
        except Exception,e:
            logging.warn("DB setup failed: %s (maybe the database is not set up correctly ?)" % e)
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
        groups = self.execute("SELECT group_active,id,group_id,group_count,modified FROM "+self.table+"  WHERE group_count AND group_active = 1 AND group_leader = -1");

        for group in groups:
                
            groupDesc = {
                "group_active" : group[0],
                "group_leader" : group[1],
                "group_id" : group[2],
                "group_count" : int(group[3]),
                "modified": group[4].timetuple()
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
            try: # Python 2.4 doesn't allow try: except: finally: together
                cursor = self.cursor_class(conn)

                query = "INSERT INTO "+self.table+" (id, host_name,host_address,type,facility,priority,program,message,alternative_message,ack,created,modified,group_active,group_id,group_leader) VALUES (%(id)s,%(host_name)s,%(host_address)s,%(type)s,%(facility)s,%(priority)s,%(program)s,%(message)s,%(alternative_message)s,%(ack)s,NOW(),NOW(),%(group_active)s,%(group_id)s,%(group_leader)s);"
            
                self.execute(query,self.get_event_params(event),noResult=True,cursor=cursor)
            
                if event.group_leader and event.group_leader > -1:
                    self.increase_group_count(event.group_id)
                else:
                    self.group_cache.add({
                        "active" : 1,
                        "group_leader" : event["id"],
                        "group_id" : event.group_id,
                        "dirty" : True
                    });
                    self.flush()
                    
                cursor.close()
                conn.commit()
                if  conn == self.spool:
                    return "SPOOL"
                return "OK"
            except Exception:
                logging.error("Insert failed : %s" % traceback.format_exc())            
                return "FAIL"
        finally:
            self.release_connection(conn)
    
    
    def get_event_params(self,event):
        event["id"] = self.next_id()
        
        params = self.out.transform(event)
        if not params:
            raise "Invalid event : %s " % event.data
        params["id"] = event["id"]
        params["group_leader"] = event.group_leader
        params["group_id"] = event.group_id
        params["alternative_message"] = event.alternative_message
        params["group_active"] = int(event.in_active_group())
        
        return params
    
    
    def increase_group_count(self,group_id):
        self.group_cache.add_new_member(group_id)
        self.flush()
     
    
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
            if not cursor:
                conn = self.acquire_connection()
                cursor = self.cursor_class(conn)
            try:
                cursor.execute(query,args)
                if self.spool and conn == self.spool:
                    self.check_spool = True
                
            except MySQLdb.OperationalError, e:
                if conn == self.spool:
                    raise
                self.check_spool = True
                if self.spool:
                    self.spool.execute(query,args)
                
                logging.warn("Query failed: %s" % e)
                return ()
            
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
    
    def execute_after_flush(self,query,args = ()):
        try:
            self.flushlock.acquire()
            self.exec_buffer.append((query,args))
        finally:
            self.flushlock.release()
            self.flush()
        
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
        try:
            conn = self.acquire_connection()
            self.group_cache.deactivate(groupId)
            self.flush()
        finally:
            self.release_connection(conn)

    def acknowledge_group(self,groupId,leader):
        query = "UPDATE "+self.table+" SET ack = 1 WHERE (group_id = %s AND group_leader = %s) OR id=%s ";
        self.execute_after_flush(query,(groupId,leader,leader)) 

    def close(self,noFlush=False):
        try:
            conn = self.acquire_connection()
            if self.flush_pending:
                self.timer.cancel()
                  
            if not noFlush:
                self.group_cache.flush_to_db(conn,self.table)
            if not noFlush and self.spool:
                self.spool.flush()
        finally:
            conn.close()
            
    def execute_spooled(self,c):
        if not self.spool:
            return
        
        
        try:
            ctr = 0
            cursor = self.cursor_class(c)
            for i in self.spool.get_spooled():
                ctr = ctr+1
                cursor.execute(i[0],i[1])
            cursor.close()
            c.commit()
            self.check_spool = False
        except Exception, e:
            logging.error("Writing spooled entries failed : %s",traceback.format_exc())
        
        
        
    def get_new_connection(self):
        try:
            c = MySQLdb.Connection(
                host=self.host,
                port=int(self.port),
                user=self.user,
                passwd=self.password,
                db=self.database
            )
            
                
            return c
        except MySQLdb.OperationalError,oe:
            logging.error(oe)
            return
            
   
    def fetch_last_id(self):
        res = self.execute("SELECT id FROM event ORDER BY id DESC LIMIT 1")
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
            
    def acquire_connection(self,noSpool=False):
        try:
            conn = self.connections.get(True,3)
            if not conn.open:
                conn = self.get_new_connection()
            
            if self.check_spool and not noSpool:
                self.execute_spooled(conn)
            return conn
        except:
            if self.spool:
                return self.spool
            else:
                raise 

    def flush_exec_queue(self,conn):
        try:
            self.flushlock.acquire()
            cursor = self.cursor_class(conn)
            for (query,args) in self.exec_buffer:
                self.execute(query,args,noResult=True,cursor=cursor)
            cursor.close()
            conn.commit()
        finally:
            self.flushlock.release()

    def _flush(self):
        try: 
            conn = self.acquire_connection()
            self.group_cache.flush_to_db(conn,self.table)
            self.flush_exec_queue(conn)
        finally:
            self.release_connection(conn)
            self.flush_pending = False
        


    def flush(self):

        if self.no_async_flush or self.flush_pending or not self.flush_lock.acquire(False):
            return
        try:
            self.timer = threading.Timer(self.flush_interval/1000,self._flush)
            self.timer.start()
            self.flush_pending = True
        
        finally:
            self.flush_lock.release()

    
    def release_connection(self,conn):
        if not conn.open:
            conn = self.get_new_connection()
        self.connections.put(conn)

    def process(self,event):
        return self.insert(event)
