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
from event import Event
from chain import ChainFactory
import signal
import logging

class Controller:
    """ Main controller. Handles factory setup and main thread creation

    """


    def __init__(self, config, instances):
        self.config = config
        self.instances = instances
        self.threads = []
        self.__setup_receptors()
        try:
            self.__read_chain_definitions()        
            self.__start_and_wait()
        finally:
            self.shutdown()
        
    
    def __setup_receptors(self):
        """ Creates all receptors defined in the *.cfg files
        """

        logging.debug("Receptors registered: %s", self.instances["receptor"])
        for id in self.instances["receptor"]:
            receptor = self.instances["receptor"][id]
            if receptor.config["format"] != None:
                receptor.config["transformer"] = receptor.config["format"]
            receptor.start()

            self.threads.append(receptor)

    def __read_chain_definitions(self):
        """ Sets up the chainfactory and loads the chain config files underneath the chain_dir

        """

        self.chainFactory = ChainFactory()
        self.chainFactory.read_config_file(self.config["chain_dir"],self.instances)


    def __start_and_wait(self):
        """ starts the receptors and waits for thread termination
            Listens on SIGQUIT and SIGINT

        """

        signal.signal(signal.SIGQUIT, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
        try:
            
            if self.instances.has_unmatched_dependencies():
                logging.warn("Unmatched dependencies found : %s",self.instances.deferred)
            while True:
                for thread in self.threads:
                    thread.join(5)

        except Exception, e:
            logging.debug(e)
        else:
            pass
        logging.debug("Attempting shutdown...")

    def shutdown(self):
        """ Graceful shutdown

        """
        logging.info("Stopping chains")
        chains = self.instances.getAllChainInstances()
        for chain in chains:
            chains[chain].stop()

        logging.info("Stopping receptors")
        for thread in self.threads:
            thread.stop()