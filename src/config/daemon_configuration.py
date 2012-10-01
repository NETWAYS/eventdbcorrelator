# 
# DAO for global RventDB Correlator configuration
# 

from optparse import OptionParser
from os import path, listdir
import ConfigParser

from config import DEFAULT_CONFIG_PATH

class DaemonConfiguration(object):
    
    def __init__(self):
        self.parse_cli();
        self.parse_config_file();
    
    def parse_cli(self):
        parser = OptionParser()
        parser.add_option("-c","--config",dest="config_file", help="use FILE as configuration",metavar="FILE",default=DEFAULT_CONFIG_PATH)
        parser.add_option("-C","--chains",dest="chain_dir", help="dir to search for event chains",default=None)
        parser.add_option("-f","--foreground",dest="foreground",action="store_true",default="False",help="run in foreground (useful for debugging")
        (self.options, args) = parser.parse_args()
        
    def parse_config_file(self): 
        if not path.exists(self.options.config_file):
            raise Exception('Config file '+self.options.config_file+" not found!")
        self.config = ConfigParser.ConfigParser()
        self.config.readfp(open(self.options.config_file))
        
        self.options.import_dir = self.config.get("global","config_dir")
        if self.options.chain_dir == None:
            self.options.chain_dir = self.config.get("global","chain_dir")
        
        if path.exists(self.options.import_dir):
            self.__read_sub_configs()
        else:
            print("Path %s not found - ignoring" % self.options.import_dir)
        
        
    def __read_sub_configs(self):
        for cfg in listdir(self.options.import_dir):
            if cfg[-3:] == "cfg":
                self.config.readfp(open(self.options.import_dir+"/"+cfg))
               
    def get_instance_definitions(self):
        res = {}
        for section in self.config.sections():
            res[section] = self.__get_section_as_dict(section)
        return res 
    
    def __get_section_as_dict(self,section):
        dict = {}
        for i in self.config.options(section):
            dict[i] = self.config.get(section,i)
        return dict
    
    def __getitem__(self,name):
        return self.options.__dict__[name]
    
    