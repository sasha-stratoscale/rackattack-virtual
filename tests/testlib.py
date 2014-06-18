import os
from rackattack import api
import socket
import time


def defaultRequirement(imageHint="hint"):
    if 'RACKATTACK_IMAGELABEL' not in os.environ:
        raise Exception("Test requires RACKATTACK_IMAGELABEL to be defined for testing")
    imageLabel = os.environ['RACKATTACK_IMAGELABEL']
    return api.Requirement(imageLabel=imageLabel, imageHint=imageHint)


def whiteboxAllocationInfo():
    return api.AllocationInfo(user="whitebox", purpose="whitebox", nice=0)


def waitForTCPServer(tcpEndpoint, timeout=3, interval=0.1):
    before = time.time()
    while time.time() - before < timeout:
        if _connect(tcpEndpoint):
            return
        time.sleep(interval)
    raise Exception("TCP Server '%(tcpEndpoint)s' did not respond within timeout" % dict(
        tcpEndpoint=tcpEndpoint))


def _connect(tcpEndpoint):
    s = socket.socket()
    try:
        s.connect(tcpEndpoint)
        return True
    except:
        return False
    finally:
        s.close()
