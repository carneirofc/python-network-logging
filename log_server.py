#!/usr/bin/python3
import argparse
import pickle
import logging
import logging.handlers
import socketserver
import struct
import os


class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    """Handler for a streaming logging request.
    This basically logs the record using whatever logging policy is
    configured locally.
    """

    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. Logs the record
        according to whatever policy is configured locally.
        """
        while True:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
            slen = struct.unpack(">L", chunk)[0]
            chunk = self.connection.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + self.connection.recv(slen - len(chunk))
            obj = self.unPickle(chunk)
            # self.client_address
            obj["msg"] = "{} {}".format(self.client_address, obj["msg"])
            record = logging.makeLogRecord(obj)
            self.handleLogRecord(record)

    def unPickle(self, data):
        return pickle.loads(data)

    def handleLogRecord(self, record):
        # if a name is specified, we use the named logger rather than the one
        # implied by the record.
        if self.server.logname is not None:
            name = self.server.logname
        else:
            name = record.name
        logger = logging.getLogger(name)
        # N.B. EVERY record gets logged. This is because Logger.handle
        # is normally called AFTER logger-level filtering. If you want
        # to do filtering, do it at the client end to save wasting
        # cycles and network bandwidth!
        logger.handle(record)


class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    """
    Simple TCP socket-based logging receiver suitable for testing.
    """

    allow_reuse_address = True

    def __init__(
        self,
        host="localhost",
        port=logging.handlers.DEFAULT_TCP_LOGGING_PORT,
        handler=LogRecordStreamHandler,
    ):
        socketserver.ThreadingTCPServer.__init__(self, (host, port), handler)
        self.abort = 0
        self.timeout = 1
        self.logname = None

    def serve_until_stopped(self):
        import select

        abort = 0
        while not abort:
            rd, wr, ex = select.select([self.socket.fileno()], [], [], self.timeout)
            if rd:
                self.handle_request()
            abort = self.abort


def main(port: int):
    tcpserver = LogRecordSocketReceiver(host="0.0.0.0", port=port)
    print("About to start TCP server...")
    tcpserver.serve_until_stopped()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Beaglebone Black serial comm log.")
    parser.add_argument(
        "--folder", "-f", help="Log folder", dest="folder", required=True
    )
    parser.add_argument(
        "--port", "-p", help="Server port", dest="port", default=9020, type=int
    )
    parser.add_argument(
        "--sufix", "-s", help="File suffix", dest="sufix", default="net_logger"
    )
    parser.add_argument("--stdout", help="log to stdout", action="store_true")
    parser.add_argument(
        "--max-bytes",
        help="Log maxBytes",
        dest="max_bytes",
        default=100000000,
        type=int,
    )
    parser.add_argument(
        "--count", help="Log backupCount", dest="count", default=10, type=int
    )
    args = parser.parse_args()

    if not os.path.exists(args.folder):
        os.makedirs(args.folder)

    feedback_logger = logging.getLogger("feedback")

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)-15s %(name)s %(levelname)s %(message)s")

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(formatter)
    consoleHandler.setLevel(logging.INFO)

    feedback_logger.addHandler(consoleHandler)

    if args.stdout:
        logger.addHandler(consoleHandler)

    else:
        handler = logging.handlers.RotatingFileHandler(
            os.path.join(args.folder, "bbb.log"),
            maxBytes=args.max_bytes,
            backupCount=args.count,
        )
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

    feedback_logger.info("Starting logging server.")
    feedback_logger.info("Settings {}".format(args))
    main(args.port)
