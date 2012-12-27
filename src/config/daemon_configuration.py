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
from optparse import OptionParser
from os import path, listdir
import ConfigParser
from config import DEFAULT_CONFIG_PATH

class DaemonConfiguration(object):
    """ Parses configuration from the cli and from the configuration file and allows easy access.
        Must work with python >= 2.4, so it uses OptionParser instead of argparse for command line arguments

    """
    def __init__(self):
        self.parse_cli();
        self.parse_config_file();
    
    def parse_cli(self):
        """ Reads options passed via stdin

        """
        parser = OptionParser()
        parser.add_option("-c","--config", dest="config_file", help="use FILE as configuration", metavar="FILE", default=DEFAULT_CONFIG_PATH)
        parser.add_option("-C","--chains", dest="chain_dir", help="dir to search for event chains", default=None)
        parser.add_option("-f","--foreground", dest="foreground", action="store_true", default=False, help="run in foreground (useful for debugging")
        parser.add_option("-l","--log", default=None, dest="log", help="Log file")
        (self.options, args) = parser.parse_args()

    def parse_config_file(self):
        """ Parses all configuration files (defined in config.py or passed via cli param --config) and reads
            all subconfigs underneath the chain_dir folder (if any)

        """
        if not path.exists(self.options.config_file):
            raise Exception('Config file '+self.options.config_file+" not found!")
        self.config = ConfigParser.ConfigParser()
        self.config.readfp(open(self.options.config_file))
        
        self.options.import_dir = self.config.get("global", "config_dir")
        if self.options.chain_dir == None:
            self.options.chain_dir = self.config.get("global", "chain_dir")
        
        if path.exists(self.options.import_dir):
            self.__read_sub_configs()
        else:
            print("Path %s not found - ignoring" % self.options.import_dir)
        
        
    def __read_sub_configs(self):
        """ Traverses through the configuration folder and reads all configurations
            found underneath

        """
        for cfg in listdir(self.options.import_dir):
            if cfg[-3:] == "cfg" and cfg[0] != ".":
                self.config.readfp(open(self.options.import_dir+"/"+cfg))
               
    def get_instance_definitions(self):
        """ Reads all object instances created in the config files

        """
        res = {}
        for section in self.config.sections():
            res[section] = self.__get_section_as_dict(section)
        return res 
    
    def __get_section_as_dict(self, section):
        """ returns a section as a key-value dictionary
            (if the section exists, otherwise an empty dict is returned)

        """
        dict = {}

        for i in self.config.options(section):
            dict[i] = self.config.get(section, i)
        return dict
    
    def __getitem__(self,name):
        """ allows to directly access cli options via the subscript operator

        """
        return self.options.__dict__[name]

    
    
