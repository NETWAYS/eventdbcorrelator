import unittest
from api.check_api_command_handler import CheckApiCommandHandler

class CheckCommandMock(object):

    def __init__(self, values):
        self.values = values
        self.values["startfrom"] = 0

    def __getitem__(self, item):
        if item in self.values:
            return self.values[item]
        return None

class DBMock(object):

    def __init__(self):
        self.queries = []
        self.table = "test"

    def execute(self, query, params):
        self.queries += (query, params)


class CheckApicommandHandlerTest(unittest.TestCase):

    def testBuildQuery(self):
        db = DBMock()

        handler = CheckApiCommandHandler(db)
        (query, params) = handler.build_query(CheckCommandMock({
        }))
        self.assertEquals([0], params)

        (query, params) = handler.build_query(CheckCommandMock({
            "host" : "hostabc"
        }))
        self.assertEquals("hostabc", params[1])
        self.assertTrue("UPPER(host_name) LIKE %s" in query)

        (query, params) = handler.build_query(CheckCommandMock({
            "host" : "hostabc",
            "message" : "Mymessage"
        }))

        self.assertEquals("hostabc", params[1])
        self.assertEquals("Mymessage", params[2])
        self.assertTrue("UPPER(host_name) LIKE %s" in query)
        self.assertTrue("message LIKE %s" in query)

        (query, params) = handler.build_query(CheckCommandMock({
            "priority" : [1,2,3,4],
            "message" : "Mymessage"
        }))


        self.assertEquals("Mymessage", params[1])
        self.assertEquals([1,2,3,4], params[2:6])
        self.assertTrue("priority IN (%s,%s,%s,%s)" in query)





