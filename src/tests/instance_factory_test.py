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
import unittest
import logging
from config import InstanceFactory

class ConfigMock(object): 
    def get_instance_definitions(self):
        return []

    
class InstanceFactoryTest(unittest.TestCase):
    
    def test_resolve_deferred(self):
        testObj = InstanceFactory(ConfigMock())
        cfg1 = {
            "class":"Mock",
            "type": "Proc",
            "blobb" : '@test2'
        }
        cfg2 = {
            "class":"Mock",
            "type": "Proc",
        }
        testObj.register("test1", cfg1, lambda id, cfg: cfg)
        
        assert testObj.has_unmatched_dependencies()
        assert cfg1["blobb"] == "@test2"        

        testObj.register("test2", cfg2, lambda id, cfg: cfg)
        assert not testObj.has_unmatched_dependencies()
        assert cfg1["blobb"] == cfg2

    def test_resolve_cfg(self):
        testObj = InstanceFactory(ConfigMock())
        testObj.instances["testmock"] = testinstance = {
            "a" : "testobject"
        }
        cfg = {
            "test" : "fuchs",
            "to_resolve" : "@testmock"
        }
        
        testObj.resolve_references(cfg)
        logging.debug(cfg)
        assert cfg["to_resolve"] == testinstance
        
