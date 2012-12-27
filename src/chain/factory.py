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
import ConfigParser
import logging
import os

from chain import Chain

__all__=['ChainFactory']


class ChainFactory(object):
    """
    Factory that handles chain registration and creation. Chains are created in a three
    step process:
    - Create and register all chains and call the setup() method directly after chain
      creation
    - After all chains are created, call the setupEventPath() method for each chain.
      As chains may reference other chains, every instance must be existing for this
      step
    - Now call the start method for each chain, causing the chain to accept events in
      a newly created thread (except "noThread" has been set in the config, but this
      should only be used for test cases)

    """

    def __init(self):
        self.chains = []
        
    def read_config_file(self, chaindir, instances):
        """ Reads all chains defined underneaht chaindir. Already created object instances are passed
            by instances.

        """
        self.instances = instances
        if not os.path.exists(chaindir):
            raise Exception("Chain configuration directory is non-existent or not readable")
        self.config_reader = ConfigParser.ConfigParser()
        self.read_dir(chaindir)
        self.create_chain_instances()
        self.wire_chains()
        self.start_chains()
        
    def read_dir(self, cur_dir):
        """ Traverses through cur_dir and parses chain definitions found there.
            Chains are *.chain files.
        """
        for cfg in os.listdir(cur_dir):
            if cfg[0] == ".":
                continue
            logging.debug("Reading chain %s ", cfg)
            filename = cur_dir+"/"+cfg
            # recursive read 
            if  os.path.isdir(filename) :
                self.read_dir(filename)
            else:
                if filename[-5:] == 'chain':
                    self.config_reader.readfp(open(filename))
        
    def create_chain_instances(self):
        """ Creates a chain defined in a configuration section

        """
        for section in self.config_reader.sections():
            self.read_chain(section)
        
    def read_chain(self, _id):
        """ reads a chain and creates the chain definition as a dictionary. This chain will be
            registered in the instancefactory
        """
        chain_def = {'class' : 'chain', 'type' : ''}
        for i in self.config_reader.options(_id):
            chain_def[i] = self.config_reader.get(_id, i)
        logging.debug("Registering chain %s", _id)
        self.instances.register(id,chain_def,self.create_chain)
 
        
    def create_chain(self, _id, config):
        """ Creates the chain instance and calls it's setup function with the configuration parameters
            defined in the chain file
        """
        chain = Chain()
        config["instances"] = self.instances
        chain.setup(_id,config)
        
        return chain

    def wire_chains(self):
        """ Sets up the event paths for each chain, so they can start processing events

        """
        allChains = self.instances.getAllChainInstances()
        for chain in allChains:
            logging.debug("%s", chain)
            allChains[chain].setup_event_path()
    
    def start_chains(self):
        """ Starts the chain

        """
        allChains = self.instances.getAllChainInstances()
        for chain in allChains:
            allChains[chain].start()
            
            