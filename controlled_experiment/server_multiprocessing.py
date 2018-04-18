#!/usr/bin/python3
''' source: https://gist.github.com/micktwomey/606178 '''
import multiprocessing
import socket
import traceback
from time import time, sleep

packetSize = 1480000
def handle(connection, address):
    connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # enable TCP_NODELAY, disable Nagle's algo
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("process-%r" % (address,))
    try:
        logger.debug("Connected %r at %r", connection, address)
        data = b'a' * packetSize + b'\n'     # data to be sent to client
        while True:
            connection.sendall(data)
            logger.debug("Sent data")
    except:
        traceback.print_exc()
        logger.exception("Problem handling request")
    finally:
        logger.debug("Closing socket")
        connection.close()

class Server(object):
    def __init__(self, hostname, port):
        import logging
        self.logger = logging.getLogger("server")
        self.hostname = hostname
        self.port = port

    def start(self):
        self.logger.debug("listening")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.hostname, self.port))
        self.socket.listen(128)

        while True:
            conn, address = self.socket.accept()
            process = multiprocessing.Process(target=handle, args=(conn, address))
            process.daemon = True
            process.start()

    def stop(self):
        self.socket.close()

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    server = Server("0.0.0.0", 8000)
    try:
        server.start()
    except:
        server.stop()
        logging.exception("Unexpected exception")
    finally:
        logging.info("Shutting down")
        for process in multiprocessing.active_children():
            logging.info("Shutting down process %r", process)
            process.terminate()
            process.join()
        server.stop()
    logging.info("All done")