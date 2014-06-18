import libvirt
import threading

_it = None


def it():
    global _it
    if _it is None:
        _it = LibvirtSingleton()
    return _it


class LibvirtSingleton:
    def __init__(self):
        self._libvirt = libvirt.open("qemu:///system")
        self._lock = threading.Lock()

    def lock(self):
        return self._lock

    def libvirt(self):
        assert not self._lock.acquire(False)
        return self._libvirt
