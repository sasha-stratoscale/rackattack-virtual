import subprocess
import logging

_LOGGER = logging.getLogger("sh")


def run(* args, ** kwargs):
    try:
        return subprocess.check_output(
            * args, stderr=subprocess.STDOUT, close_fds=True, ** kwargs)
    except subprocess.CalledProcessError as e:
        _LOGGER.exception(
            "Return code:%(returncode)d Output was:\n%(output)s",
            dict(output=e.output, returncode=e.returncode))
        raise
