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
from receptors.abstract_receptor import AbstractReceptor


class RequestHandler(AbstractReceptor):

    def setup(self, client, config):
        self.client = client
        self.config = config

    def run(self):

        msg = self.client.recv(self.config["bufferSize"])
        try:
            if not msg == "":
                cmd = self.config["commandCls"](msg)
                if cmd.valid:
                    result = self.config["commandHandler"].handle(cmd)
                    self.client.send(pickle.dumps(result))
                else:
                    self.client.send(pickle.dumps({
                        "error" : "Invalid request send"
                    }))
        except Exception, e:
            logging.error(e)
            self.client.send(pickle.dumps({
                "error" : e
            }))

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

        if not "datasource" in config:
            logging.error("Non operational api, as no datasource is given. This will crash.")
            return
        self.config["datasource"] = config["datasource"]

        if "commandHandler" in config:
            self.config["commandHandler"] = config["commandHandler"](config["datasource"])
        else:
            self.config["commandHandler"] = CheckApiCommandHandler(config["datasource"])

        self.run_flags = os.O_RDONLY|os.O_NONBLOCK
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
                conn, addr = self.socket.accept()
                client.setup(conn, self.config)
                client.start()
            except socket.error, err:
                if err.errno == 11:
                    continue
                else:
                    raise err
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

        self.socket.close()


    def _read(self):
        """ Reads from the pipe and transforms raw event strings to Api Commands

        """
        buffersize = self.config["bufferSize"]
        self.last_part = ""
        while self.running:
            inPipes, pout, pex = select.select([self.pipe], [], [], 3)

            if len(inPipes) > 0:
                pipe = inPipes[0]
                try:
                    data_packet = os.read(pipe, buffersize)
                except OSError, e:
                    # EAGAIN means the pipe would block
                    # on reading, so try again later
                    if e.errno == 11:
                        continue
                    else:
                        raise e
                if len(data_packet) == 0:
                    self.__reopen_pipe()
                    continue
                messages = self._get_messages_from_raw_stream(data_packet)

                for message in messages:
                    if message == "":
                        continue
                    transformed = self.create_command(message)

                    if self.queues and transformed:
                        if isinstance(transformed, CheckCommand):
                            transformed["source"] = self.source
                        for queue in self.queues:
                            queue.put(transformed)
                    if self.callback != None:
                        self.callback(self, transformed)

            else:
                if self.callback != None:
                    self.callback(self)
                continue
            if "noThread" in self.config:
                return
