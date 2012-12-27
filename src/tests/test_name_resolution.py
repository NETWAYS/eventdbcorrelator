

import unittest
from network.address_resolver import DynamicAddressResolver

class NameResolutionTestCase(unittest.TestCase):

    def test_ip_to_name_dynamic(self):
        resolver = DynamicAddressResolver()
        assert resolver.get_hostname("127.0.0.1") == "localhost"
        assert resolver.get_hostname("127.0.0.15") == "127.0.0.15"
        assert resolver.get_hostname("555.0.0.15") == "555.0.0.15"
        assert resolver.get_hostname("test") == "test"

    def test_name_to_ip_dynamic(self):
        resolver = DynamicAddressResolver()
        assert resolver.get_ip_address("localhost") == "127.0.0.1"
        assert resolver.get_ip_address("idontexistinthenetwork") == "idontexistinthenetwork"
