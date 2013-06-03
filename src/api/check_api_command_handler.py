import logging
import time


class CheckApiCommandHandler(object):


    def __init__(self, db):
        self.db = db


    def handle(self, command):
        query, params = self.build_query(command)
        try:
            result =  self.db.execute(query,params)
        except Exception, e:
            return {
                "error" : e
            }
        if len(result) < 1:
            result = ((0,0,0,0))
        db_result = {
            "total" : result[0][0],
            "last_id" : result[0][1],
            "nr_of_warnings" : result[0][2],
            "nr_of_criticals" : result[0][3],
            "message" : None
        }
        if not db_result["last_id"] is None:
            message = self.db.execute(
                "SELECT message FROM "+self.db.table+" WHERE id = %s",
                [db_result["last_id"]]
            )
            if len(message) > 0:
                db_result["message"] = message[0][0]
        return db_result


    def build_query(self, cmd):
        (query, params) = self.get_base_query(cmd)

        if cmd["host"] is not None:
            query += " AND UPPER(host_name) LIKE %s"
            params.append(cmd["host"])

        if cmd["message"] is not None:
            query += " AND message LIKE %s"
            params.append(cmd["message"])

        if cmd["priority"] is not None:
            query += " AND priority IN (%s)" % self.get_in_placeholder_for(cmd["priority"])
            params += cmd["priority"]

        if cmd["facility"] is not None:
            query += " AND facility IN (%s)" % self.get_in_placeholder_for(cmd["facility"])
            params += cmd["facility"]

        if cmd["logtype"] is not None:
            query += " AND type IN (%s)" % self.get_in_placeholder_for(cmd["logtype"])
            params += cmd["logtype"]

        if cmd["maxage"] is not None:
            query += " AND created >= '%02d-%02d-%02d %02d:%02d:%02d'" % time.localtime(cmd["maxage"])[0:6]


        if cmd["program"] is not None:
            query += " AND program IN (%s)" % self.get_in_placeholder_for(cmd["program"])
            params += cmd["program"]

        if cmd["ipaddress"] is not None:
            query += " AND host_address = %s"
            params.append(cmd["ipaddress"])

        if cmd["ack"] is not None:
            query += " AND ack = 0"
        return query, params

    def get_in_placeholder_for(self,ids):
        return ','.join(['%s'] * len(ids))

    def get_count_field(self, values, field):
        if values is None:
            return " COUNT(id) AS "+field+" ", None
        caseQuery = "CASE WHEN priority IN (%s) THEN 1 ELSE 0 END" % self.get_in_placeholder_for(values)
        return " SUM("+caseQuery+") AS "+field+" ", values


    def get_base_query(self, cmd):
        warning_count_field, warning_prios = \
            self.get_count_field(cmd["prio_warning"],"count_warning")
        critical_count_field, critical_prios = \
            self.get_count_field(cmd["prio_critical"],"count_critical")
        params = []
        if not warning_prios is None:
            params += warning_prios
        if not critical_prios is None:
            params += critical_prios

        queryBase = "SELECT COUNT(id) AS count, MAX(id) AS last, %s, %s FROM %s WHERE id > "
        queryBase = queryBase % (warning_count_field, critical_count_field, self.db.table)
        queryBase += "%s "
        params.append(cmd["startfrom"])

        return queryBase, params


