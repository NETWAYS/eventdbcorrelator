import abstract_datasource
import MySQLdb
import logging
import db_transformer
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
class MysqlDatasource(abstract_datasource.AbstractDatasource):
    def setup(self,id,config):
        self.id = id
        self.host = config["host"]
        self.port = config["port"]
        self.user = config["user"]
        self.password = config["password"]
        self.database = config["database"]
        self.table = config["table"]
        if "transform" in config:
            self.out = config["transform"]
        else:
            self.out = db_transformer.DBTransformer()
        self.connection = False
        self.connect()
        
    def connect(self):
        if self.connection and self.connection.open == 1:
            return
                    
        self.connection = MySQLdb.connection(
            host=self.host,
            port=int(self.port),
            user=self.user,
            passwd=self.password,
            db=self.database
        )

        logging.debug(self.connection)
    
    def is_available(self):
        connect()
        return self.connection != None
    
    def insert(self,event):
        query = "INSERT INTO "+self.table+" (host_name,host_address,type,facility,priority,program,message,ack,created,modified) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        self.execute(query,self.out.transform(event))
        
    def remove(self,event):
        query = "DELETE FROM %s WHERE id = %i" % (self.table,event["db_primary_id"])
        self.execute(query)
        
    def update(self,event):
        query = "UPDATE TABLE "+self.table+" SET host_name = %s, host_address = %s ,type = %s,facility = %s,priority = %s,program = %s,message = %s,ack = %s,created = %s,modified = %s WHERE id = "+event["db_primary_id"]
        self.execute(query)
    
    def execute(self,query,args = ()):
        try:
            self.connect()
            cursor = self.connection.cursor()
            if self.connection == None or not self.connection.open:
                return False
            result = cursor.execute(query,args)
            result.commit()
        finally:
            cursor.close()
    
    def close(self):
        if self.connection != None and self.connection.open == 1:
            self.connection.close()