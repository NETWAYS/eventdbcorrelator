from _socket import SOCK_DGRAM
import logging
from api.check_api_command_handler import CheckApiCommandHandler
from api.check_command import CheckCommand
import select
import pickle
import socket
import threading
import pwd
import os
import time
from receptors.abstract_receptor import AbstractReceptor


class RequestHandler(AbstractReceptor):

    def setup(self, client, config):
        self.client = client
        self.config = config

    def run(self):
        msg = None
        try:
            msg = self.client.recv(self.config["bufferSize"])
        except Exception, e:
            logging.error("Error while reading: %s" % e)

        if msg is None or msg == "":
            self.client.close()
            return

        logging.debug(self.getName() + ": got request: %s" % msg)

        reply = None
        try:
            cmd = self.config["commandCls"](msg)
            if cmd.valid:
                result = self.config["commandHandler"].handle(cmd)
                reply = pickle.dumps(result)
            else:
                reply = pickle.dumps({
                    "error" : "Invalid request send"
                })
        except Exception, e:
            logging.error("Error while processing command: %s" % e)
            reply = pickle.dumps({
                "error" : e
            })

        try:
            if reply is not None:
                logging.debug(self.getName() + ": sending reply")
                self.client.send(pickle.dumps(result))
        except Exception, e:
            logging.error("Error while sending reply: %s" % e)

        logging.debug(self.getName() + ": finished.")

        # make sure to close connection
        self.client.close()


class CheckapiReceptor(threading.Thread):

    def setup(self, _id, config):
        """ Default setup method as called by the InstanceFactroy, sets up the pipe
            but doesn't start the read operation yet

        """
        self.id = _id
        self.running = False
        self.callback = None
        self.config = {
            "mod" : 0666,
            "owner" : os.getuid(),
            "group" : os.getgid(),
            "path" : "/usr/local/var/edbc.cmd",
            "bufferSize" : 4096,
            "commandCls" : CheckCommand
        }

        self.threads = []

        if not "datasource" in config:
            logging.error("Non operational api, as no datasource is given. This will crash.")
            return
        self.config["datasource"] = config["datasource"]

        if "commandHandler" in config:
            self.config["commandHandler"] = config["commandHandler"](config["datasource"])
        else:
            self.config["commandHandler"] = CheckApiCommandHandler(config["datasource"])

        for key in config.keys():
            if key == 'owner':
                config[key] = pwd.getpwnam(config[key]).pw_uid
            else:
                if key == 'group':
                    config[key] = pwd.getpwnam(config[key]).pw_gid
                else:
                    self.config[key] = config[key]

        self.socket = None
        self.queues = []
        self.setup_socket()

    def create_command(self, message):
        return self.config["commandCls"](message)

    def setup_socket(self):
        logging.debug("Setting up socket %s" % self.config["path"])

        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, 0)
        if os.path.exists(self.config["path"]):
            os.unlink(self.config["path"])
        self.socket.bind(self.config["path"])
        self.socket.listen(30)

    def start(self, queue=[], cb=None):
        """ Starts the receptor in a new thread

        """
        if not queue:
            queue = []
        if isinstance(queue, (list, tuple)):
            self.queues = queue
        else:
            self.queues = [queue]

        if cb != None:
            self.callback = cb

        if "noThread" in self.config: # this is only for testing
            #logging.debug("Threading disabled for PipeReceptor")
            return self.run()
        return super(CheckapiReceptor, self).start()

    def run(self):
        self.running = True

        while self.running:
            try:
                client = RequestHandler()
                # try to accept connection
                conn = None
                addr = None
                try:
                    logging.debug("wait for connect: %s" % self.getName())
                    self.socket.settimeout(0.500)
                    conn, addr = self.socket.accept()
                except socket.timeout:
                    time.sleep(1) # wait until next try to accept
                    logging.debug("retry accept: %s" % self.getName())

                if conn is not None:
                    client.setup(conn, self.config)
                    logging.debug("start thread: " + client.getName())
                    client.start()
                    self.threads.append(client)

            except Exception, e:
                logging.error("Error while processing request: %s" % e)

            for thread in self.threads:
                if not thread.isAlive():
                    logging.debug("removing thread: %s" % thread.getName())
                    self.threads.remove(thread)
                    thread.join()

            logging.debug("running threads: %d" % len(self.threads))

        try:
            self.socket.close()
        except:
            pass

    def stop(self):
        self.running = False

        try:
            killsocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, 0)
            killsocket.connect(self.config["path"])
            killsocket.send("")
            killsocket.close()
        except socket.error, err:
            if not err.errno == 32: # broken pipe is fine her
                logging.info("Exception during shutdown (harmless): %s ", err)

        for thread in self.threads:
            thread.join(1.0)

        try:
            self.socket.close()
        except:
            pass


