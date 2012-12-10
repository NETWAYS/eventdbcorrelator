"""
EDBC - Message correlation and aggregation engine for passive monitoring events
Copyright (C) 2012  NETWAYS GmbH

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""
import MySQLdb
import MySQLdb.cursors
import Queue
import traceback
import threading
from event import Event
import logging
from datasource import db_transformer
import time

LOCATION_SETUP_SCHEME = "./database/mysql_create.sql"
LOCATION_TEARDOWN_SCHEME = "./database/mysql_teardown.sql"
MAX_INSERT_TRIES = 5

class MysqlGroupCache(object):
    """ Internal helper class for caching grouped event states
    
    Internal helper class that manages event group states and allows to 
    flush multiple group changes (like acknowledgment) in batched 
    transactions. This prevents event bursts from crashing the db and
    keeps edbc from using selects to gather the current state (and therefore
    prevents unneccessary mysql cache flushes)
    """
    
    
    def __init__(self):
        self.lock = threading.Lock()
        self.deprecated_groups = []
        self.groups = {}
        
    def add(self, group):
        """ Adds a group to the cache or creates a new one if necessary

        """
        self.groups[group["group_id"]] = group
        group["dirty"] = False
        if not "group_active" in group:
            group["group_active"] = 1
        if not "modified" in group:
            self.add_new_member(group["group_id"])

    def clear(self, group_id):
        """ Clears the cache by removing all events

        """ 
        try:
            self.lock.acquire()
            if group_id in self.groups: 
                del self.groups[group_id] 
        finally:
            self.lock.release()

    def add_new_member(self, group_id):
        """ Adds a new member to the group with id group_id

        Basically this method updates the group count for the group, sets
        the dirty flag and updates the modified timestamp
        """
        self.lock.acquire()
        try:
            if not group_id in self.groups:
                return
            if not "group_count" in self.groups[group_id]:
                self.groups[group_id]["group_count"] = 0
            group = self.groups[group_id]
            group["group_count"] = group["group_count"]+1
            group["modified"] = time.localtime()
            group["dirty"] = True
        finally:
            self.lock.release()
   
    def deactivate(self, group_id):
        """ Deactivates the group with group_id by setting group_active to 0 

        """      
        self.lock.acquire()
        try:
            if not group_id in self.groups:
                return

            self.groups[group_id]["group_active"] = 0
            self.groups[group_id]["dirty"] = True

            # Move this group to the deprecated_groups array
            # so it gets flushed properly in case a new group
            # with the same id is created
            self.deprecated_groups.append(self.groups[group_id])
            del self.groups[group_id]
        finally:
            self.lock.release()
        
    
    def get(self, group_id):
        """" Returns an active group with the specified group id or None
  
        """    
        try:
            self.lock.acquire()
            if group_id in self.groups and \
                    self.groups[group_id]["group_active"] == 1:
                return self.groups[group_id]
            
            return None
        finally:
            self.lock.release()
       
    def flush_deprecated_to_db(self, cursor, table):
        """ Internal method that flushes inactive groups to the database
    
        """ 
        for group in self.deprecated_groups:
            group["modified_ts"] = time.mktime(group["modified"])
            cursor.execute("UPDATE "+table+" SET "+
                    "group_active=%(group_active)s, "+
                    "group_autoclear=%(group_autoclear)s, "+
                    "modified=FROM_UNIXTIME(%(modified_ts)s), "+
                    "group_count=%(group_count)s "+
                    "WHERE id=%(group_leader)s OR "+
                    "group_leader=%(group_leader)s", group)
        self.deprecated_groups = [] 
        
    def flush_to_db(self, conn, table):
        """ Flushes the content of this cache to the given table and connection

        """
        cursor = conn.cursor()
        try:
            self.lock.acquire()
            self.flush_deprecated_to_db(cursor, table)  

            for groupId in self.groups:
                group = self.groups[groupId]
                if not group["dirty"]:
                    continue
                group["modified_ts"] = time.mktime(group["modified"])
                cursor.execute("UPDATE "+table+" SET "+
                    "group_active=%(group_active)s, "+
                    "group_autoclear=%(group_autoclear)s, "+
                    "modified=FROM_UNIXTIME(%(modified_ts)s), "+
                    "group_count=%(group_count)s "+
                    "WHERE id=%(group_leader)s", group)
                group["dirty"] = False
                if not group["group_active"]:
                    self.clear(groupId)
        finally:
            conn.commit()
            cursor.close()
            self.lock.release()
            
        
class MysqlDatasource(object):
    """ Mysql Datasource implementation
    
    Writes events to the database, handles group management and caches state 
    information (like the next id or active groups) to allow fast event state
    access.
    """

    def __init__(self):
        self.available_connections = []
        self.connections = Queue.Queue()
        self.lock = threading.Lock()
        self.flushlock = threading.Lock()
        self.exec_buffer = []
        self.check_spool = True
        self.flush_pending = False
        self.flush_lock = threading.Lock()

    def setup(self, _id, config):
        """ Setup method that configures the instance of this method

        InstanceFactory calls this with the id and configuration from datasource
        definitions defined in the conf.d directory
        """
        self.id = _id
        self.host = config["host"]
        self.port = config["port"]
        self.user = config["user"]
        self.password = config["password"]
        self.database = config["database"]

        if "flush_interval" in config:
            self.flush_interval = float(config["flush_interval"])
        else:
            self.flush_interval = 100.0

        if "no_flush" in config:
            self.no_async_flush = True
        else:
            self.no_async_flush = False

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
       
        #TODO: Pooling causes deadlocks at this time, so always ignore it
        self.poolsize = 1
            
        if "table" in config:
            self.table = config["table"]
        else:
            self.table = "event"
        if "transform" in config:
            self.out = config["transform"]
        else:
            self.out = db_transformer.DBTransformer()
         
        self.connect()
        try:
            self._fetch_active_groups()
            self.fetch_last_id()
        except Exception, exc:
            logging.warn("DB setup failed: %s "+
                "(maybe the database is not set up correctly ?)" % exc) 

    def connect(self):
        """ Refill the connection list with new database connections if necessary

        """
        if not self.connections.empty():
            return
        
        for i in range(0, self.poolsize):
            c = self.get_new_connection()
            if c :
                self.connections.put(c)
                self.available_connections.append(c)


    def _fetch_active_groups(self):
        """ Updates the internal group cache from the db

        """ 
        self.group_cache = MysqlGroupCache()
        groups = self.execute("SELECT group_active,id,group_id,group_count,"+
                "modified,group_autoclear FROM "+self.table+" "+
                "WHERE group_count AND group_active = 1 "+
                "AND group_leader = -1")

        for group in groups:
            groupDesc = {
                "group_active" : group[0],
                "group_leader" : group[1],
                "group_id" : group[2],
                "group_count" : int(group[3]),
                "modified": group[4].timetuple(),
                "group_autoclear" : group[5]
            }
            self.group_cache.add(groupDesc)

    def test_setup_db(self):
        """ Test method that creates the database from a given db scheme

        Only use this to initialize the db for unittests
        """ 
        sql_file = open(LOCATION_SETUP_SCHEME,'r')
        setup_sql = ""
        for line in sql_file:
            setup_sql += "%s" % line
        self.execute(setup_sql)
        self._fetch_active_groups()

        self.fetch_last_id()

    def test_teardown_db(self):
        """ Test method that tears down the database from a given db scheme
    
        Only use this to reset the db state after a unittest is complete
        """
        sql_file = open(LOCATION_TEARDOWN_SCHEME,'r')
        setup_sql = ""
        for line in sql_file:
            setup_sql += "%s" % line
        self.execute(setup_sql)        

    
    def test_clear_db(self):
        """ Test method that sets up a clean database
    
        Use this at the beginning of your unittests
        """
        self.test_teardown_db()
        self.test_create_db()


    def insert(self, event):
        """ Inserts an event in the database. 

        The actually insert might occur later depending if the datasource
        caches events and flushes them (which is the case, in general)
        """ 
        conn = self.acquire_connection()
        try: 
            try: # Python 2.4 doesn't allow try: except: finally: together
                cursor = self.cursor_class(conn)

                for i in range(0, MAX_INSERT_TRIES):        
                    try: 
                        query = "INSERT INTO "+self.table+\
                            " (id, host_name,host_address,type,facility,"+\
                            "priority,program,message,alternative_message,ack"+\
                            ",created,modified,group_active,group_id,"+\
                            "group_autoclear,group_leader) VALUES "+\
                            "(%(id)s,%(host_name)s,%(host_address)s,%(type)s,"+\
                            "%(facility)s,%(priority)s,%(program)s,"+\
                            "%(message)s,%(alternative_message)s,%(ack)s,"+\
                            "NOW(),NOW(),%(group_active)s,%(group_id)s,"+\
                            "%(group_autoclear)s,%(group_leader)s);"
                        self.execute(query, self.get_event_params(event),
                                            no_result=True, cursor=cursor)
                        break
                    except MySQLdb.IntegrityError, exc:
                        # maybe another process wrote to the db and now
                        # there's primary key confusion
                        # Refreshing the id from the db should fix that
                        self.fetch_last_id(cursor=cursor, step=i*MAX_INSERT_TRIES)
                        if i >= MAX_INSERT_TRIES-1:
                            raise exc
                        continue
                    
                if event.group_leader and event.group_leader > -1:
                    self.increase_group_count(event.group_id)
                else:
                    self.group_cache.add({
                        "active" : 1,
                        "group_leader" : event["id"],
                        "group_id" : event.group_id,
                        "dirty" : True,
                        "group_autoclear" : event["group_autoclear"]
                    })
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
    

    def get_event_params(self, event):
        """ Returns the transformed (i.e. database ready) parameters from an event
    
        """ 
        event["id"] = self.next_id()
        
        params = self.out.transform(event)
        if not params:
            raise "Invalid event : %s " % event.data

        params["id"] = event["id"]
        params["group_leader"] = event.group_leader
        params["group_id"] = event.group_id
        params["alternative_message"] = event.alternative_message
        params["group_active"] = int(event.in_active_group())
        params["group_autoclear"] = event["group_autoclear"]
        return params
    
    def increase_group_count(self, group_id):
        """ Informs the cache that a new member is in the the group with group_id)

        """
        self.group_cache.add_new_member(group_id)
        self.flush()
     
    def remove(self, event):
        """ Removes an event from the database by setting it to active=0

        """
        query = "UPDATE %s SET active=0 WHERE id = %i" \
                            % (self.table, event["id"])
        self.execute(query)
     
    def update(self, event):
        """ Updates an existing event

        """
        query = "UPDATE "+self.table+" SET host_name=%(host_name)s, "+\
                "host_address=%(host_address)s,type=%(type)s,"+\
                "facility=%(facility)s,priority=%(priority)s,"+\
                "program=%(program)s,message=%(message)s,"+\
                "ack=%(ack)s,created=%(created)s,modified=%(modified)s "+\
                "WHERE id = "+str(event["id"])
        self.execute(query, self.out.transform(event), no_result=True)
        
    def execute(self, query, args = (), no_result=False, cursor=None):
        """ Performs an arbitary sql query on this mysql datasource
    
        If no_result is given, no fetch operation is executed after the query.
        If the execution is part of a bigger execution batch, a cursor can
        be provided, otherwise the method will create one by itself
        
        """
        cursor_given = cursor != None
        conn = None
        try:
            if not cursor:
                conn = self.acquire_connection()
                cursor = self.cursor_class(conn)
            try:
                cursor.execute(query, args)
                if self.spool and conn == self.spool:
                    self.check_spool = True
                
            except MySQLdb.OperationalError, e:
                if conn == self.spool:
                    raise
                self.check_spool = True
                if self.spool:
                    self.spool.execute(query, args)
                
                logging.warn("Query failed: %s" % e)
                return ()
            
            if not no_result:
                result = cursor.fetchall()
                return result
            
            return ()
        finally:
            
            if cursor != None and not cursor_given:
                cursor.close()
            if conn:
                conn.commit()
                self.release_connection(conn)
   
    def execute_after_flush(self, query, args = ()):
        """Queues an query to be executed at the next flush
    
        """
        try:
            self.flushlock.acquire()
            self.exec_buffer.append((query, args))
        finally:
            self.flushlock.release()
            self.flush()
       
    def get_event_by_id(self, event_id):    
        """ Returns an event with the given id from the database

        """ 
        eventfields = ("id", "host_name", "host_address", "type", "facility",
                    "priority","program","message","alternative_message","ack",
                    "created","modified","group_id","group_leader",
                    "group_active")
        event = self.execute("SELECT %s FROM event WHERE id = %i AND active = 1 " \
                        % (",".join(eventfields), int(event_id)))
    
        if len(event) < 1:
            return None
        return Event(record={"data": event[0], "keys": eventfields})
        
    def get_group_leader(self, group_id):
        """ Returns the event that acts as the group leader of the given group id
    
        """

        group = self.group_cache.get(group_id)
        
        if not group:
            return (None, None)
        return (group["group_leader"], time.mktime(group["modified"]))
    
    def deactivate_group(self, group_id):
        """ Deactivates the given group_id

        """
        try:
            conn = self.acquire_connection()
            self.group_cache.deactivate(group_id)
            self.flush()
        finally:
            self.release_connection(conn)
   
    def acknowledge_group(self, group_id, leader):
        """ Acknowledge a complete group in the next flush

        """
        query = "UPDATE "+self.table+\
                " SET ack = 1 WHERE (group_id = %s AND group_leader = %s)"+\
                " OR id=%s "
        self.execute_after_flush(query, (group_id, leader, leader)) 
    
    def close(self, no_flush=False):
        """ Closes all connections and flushes pending queries if no_flush isn't set

        """
        try:
            conn = self.acquire_connection()
            if self.flush_pending:
                self.timer.cancel()
                  
            if not no_flush:
                self.group_cache.flush_to_db(conn, self.table)
            if not no_flush and self.spool:
                self.spool.flush()
        finally:
            conn.close()

    def execute_spooled(self, conn):
        """ Executes queries from the spool provider - if any is given

        """       
        if not self.spool:
            return
        
        try:
            ctr = 0
            cursor = self.cursor_class(conn)
            for spooled in self.spool.get_spooled():
                ctr = ctr+1
                cursor.execute(spooled[0], spooled[1])
            cursor.close()
            conn.commit()
            self.check_spool = False
        except Exception, exc:
            logging.error("Writing spooled entries failed : %s", exc)
        
    
    def get_new_connection(self):
        """ Returns a new connection

        """ 
        try:
            conn = MySQLdb.Connection(
                host=self.host,
                port=int(self.port),
                user=self.user,
                passwd=self.password,
                db=self.database
            )
            return conn
        except MySQLdb.OperationalError, oexc:
            logging.error(oexc)
            return
    
    def fetch_last_id(self, cursor = None, step=0):
        """ Updates the internal id counter from the db
    
        """
        res = self.execute("SELECT id FROM event ORDER BY id DESC LIMIT 1",
                            cursor=cursor)
        if len(res) < 1:
            self.last_id = 0
            return
        self.last_id = res[0][0]+step
       
    def next_id(self):
        """ Returns the next possible primary key id for event insertion

        """ 
        try:
            self.lock.acquire()
            self.last_id = self.last_id+1
            return self.last_id
        finally:
            self.lock.release()
        
    def acquire_connection(self, no_spool=False):
        """ Returns a connection from the connection queue

        Acquired connections must be freed with release_connection
        """ 
        try:
            conn = self.connections.get(True, 3)
            if not conn.open:
                conn = self.get_new_connection()
            
            if self.check_spool and not no_spool:
                self.execute_spooled(conn)
            return conn
        except Exception, exc:
            if self.spool:
                logging.warn("Could not acquire connection, using spool (%s)", exc)
                return self.spool
            else:
                return self.acquire_connection(no_spool)
    
    def flush_exec_queue(self, conn):
        """ Flushes the query cache and executes queued queries
    
        """
        try:
            self.flushlock.acquire()
            cursor = self.cursor_class(conn)
            for (query, args) in self.exec_buffer:
                self.execute(query, args, no_result=True, cursor=cursor)
            cursor.close()
            conn.commit()
        finally:
            self.flushlock.release()

    def _flush(self):
        """ Executes the query flush operation

        """
        conn = self.acquire_connection()
        try: 
            self.group_cache.flush_to_db(conn, self.table)
            self.flush_exec_queue(conn)
        finally:
            self.release_connection(conn)
            self.flush_pending = False

    def flush(self):
        """ Triggers a flush after flush_interval seconds
        
        """
        if self.no_async_flush or self.flush_pending \
                    or not self.flush_lock.acquire(False):
            return
        try:
            self.timer = threading.Timer(self.flush_interval/1000, self._flush)
            self.timer.start()
            self.flush_pending = True
        
        finally:
            self.flush_lock.release()

    def release_connection(self, conn):
        """ Returns a database connection to the database connection pool

        """
        if not conn.open:
            conn = self.get_new_connection()
        self.connections.put(conn)
    
    def process(self, event):
        """ Standard chain element process method - triggers insert()

        """
        return self.insert(event)


