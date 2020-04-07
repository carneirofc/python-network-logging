#!/usr/bin/env python3
import sys
import argparse
import logging
import logging.handlers


def parse():
    parser = argparse.ArgumentParser("Remote logging")
    parser.add_argument("--ip", help="Server ip.", dest="ip", required=True)
    parser.add_argument("--port", help="Server port.", dest="port", default=9020)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse()

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(levelname)s] %(message)s", datefmt="%d/%m/%Y %H:%M:%S.%f"
    )

    socketHandler = logging.handlers.SocketHandler(args.ip, args.port)
    socketHandler.setFormatter(formatter)
    socketHandler.setLevel(logging.DEBUG)
    logger.addHandler(socketHandler)
    logger.info("Network logging enable {}.".format(args.ip))

    for line in sys.stdin:
        logger.info(line.rstrip())
