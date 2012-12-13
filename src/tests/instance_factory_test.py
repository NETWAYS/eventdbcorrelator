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
from config import InstanceFactory

class ConfigMock(object):
    """ Mock that acts as a dependency placeholder for object setup
    """
    def get_instance_definitions(self):
        return []

    
class InstanceFactoryTest(unittest.TestCase):
    
    def test_resolve_deferred(self):
        """ Test if processors with dependencies to not yet created processors
            are correctly deferred
        """
        
        test_obj = InstanceFactory(ConfigMock())
        cfg1 = {
            "class":"Mock",
            "type": "Proc",
            "blobb" : '@test2'
        }
        cfg2 = {
            "class":"Mock",
            "type": "Proc",
        }
        test_obj.register("test1", cfg1, lambda id, cfg: cfg)
        
        assert test_obj.has_unmatched_dependencies()
        assert cfg1["blobb"] == "@test2"        

        test_obj.register("test2", cfg2, lambda id, cfg: cfg)
        assert not test_obj.has_unmatched_dependencies()
        assert cfg1["blobb"] == cfg2

    def test_resolve_cfg(self):
        """ Test resolving of @instance references

        """
        test_obj = InstanceFactory(ConfigMock())
        test_obj.instances["testmock"] = testinstance = {
            "a" : "testobject"
        }
        cfg = {
            "test" : "fuchs",
            "to_resolve" : "@testmock"
        }
        
        test_obj.resolve_references(cfg)
        assert cfg["to_resolve"] == testinstance
        
