import signal
import sys
import logging


def _informIntSignalCaughtAndExit(* args):
    logging.info("Caught Ctrl-C, exiting from process")
    sys.exit()


def _informTermSignalCaughtAndExit(* args):
    logging.info("SIGTERM received, exiting from process")
    sys.exit(143)


def _register():
    signal.signal(signal.SIGTERM, _informTermSignalCaughtAndExit)
    signal.signal(signal.SIGINT, _informIntSignalCaughtAndExit)


_register()
