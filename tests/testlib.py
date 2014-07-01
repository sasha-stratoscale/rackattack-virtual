from rackattack import api
import socket
import time
import subprocess


def defaultRequirement(imageHint="vanilla"):
    labelRegex = "solvent__rootfs-vanilla__rootfs__.*__clean"
    lines = subprocess.check_output(["osmosis", "listlabels", labelRegex]).strip()
    if len(lines) == 0:
        raise Exception("Local osmosis object store does not contain a label matching '%s'" % labelRegex)
    imageLabel = lines.split("\n")[0]
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
