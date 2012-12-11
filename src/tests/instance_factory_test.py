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
        
