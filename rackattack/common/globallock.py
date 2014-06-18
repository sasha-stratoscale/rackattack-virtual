import threading


lock = threading.Lock()


def assertLocked():
    assert not lock.acquire(False)
    return True
