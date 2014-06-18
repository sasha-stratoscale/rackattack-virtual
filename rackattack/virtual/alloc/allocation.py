from rackattack.virtual.kvm import vm
from rackattack.virtual.kvm import config
from rackattack.common import hoststatemachine
from rackattack.common import globallock
from rackattack.common import timer
from rackattack.virtual.alloc import acumulate
import time


class Allocation:
    _LIMBO_AFTER_DEATH_DURATION = 60
    _HEARTBEAT_TIMEOUT = 15

    def __init__(self, index, tftpboot, inaugurate, hosts, freePool, stateChangeCallback, requirements):
        self._index = index
        self._tftpboot = tftpboot
        self._inaugurate = inaugurate
        self._hosts = hosts
        self._freePool = freePool
        self._requirements = requirements
        self._stateChangeCallback = stateChangeCallback
        self._acumulate = acumulate.Acumulate(
            tftpboot=tftpboot, inaugurate=inaugurate, hosts=hosts, freePool=freePool)
        self._waiting = dict()
        self._allocated = dict()
        self._death = None
        if len(self._requirements) > config.MAXIMUM_VMS:
            self._die(
                "Configured to disallow such a large allocation. Maximum is %d" % config.MAXIMUM_VMS)
            return
        self.heartbeat()
        self._freePool.registerPutListener(self._attemptToAllocate)
        self._attemptToAllocate()

    def index(self):
        return self._index

    def allocated(self):
        assert self.done()
        return self._allocated

    def done(self):
        done = len(self._allocated) == len(self._requirements)
        assert not done or len(self._waiting) == 0
        return done

    def free(self):
        self._die("freed")

    def heartbeat(self):
        if self.dead():
            return
        timer.cancelAllByTag(tag=self)
        timer.scheduleIn(timeout=self._HEARTBEAT_TIMEOUT, callback=self._heartbeatTimeout, tag=self)

    def dead(self):
        assert self._death is None or self._allocated is None
        if self._death is None:
            return None
        return self._death['reason']

    def deadForAWhile(self):
        if not self.dead():
            return False
        return self._death['when'] < time.time() - self._LIMBO_AFTER_DEATH_DURATION

    def _heartbeatTimeout(self):
        self._die("heartbeat timeout")

    def _die(self, reason):
        assert not self.dead()
        self._acumulate.free()
        self._allocated = None
        self._waiting = None
        self._death = dict(when=time.time(), reason=reason)
        timer.cancelAllByTag(tag=self)
        self._stateChangeCallback(self)

    def _attemptToAllocate(self):
        for name in self._notAllocated():
            self._attemptAllocationMethod(name, self._acumulate.tryAllocateFromFreePoolWithHint)
        for name in self._notAllocated():
            self._attemptAllocationMethod(name, self._acumulate.tryAllocateFromFreePool)
        for name in self._notAllocated():
            self._attemptAllocationMethod(name, self._acumulate.tryCreate)
        for name in self._notAllocated():
            self._attemptAllocationMethod(name, self._acumulate.tryDestroyFromFreePoolAndCreate)
        if len(self._notAllocated()) == 0:
            self._freePool.unregisterPutListener(self._attemptToAllocate)

    def _notAllocated(self):
        return set(self._requirements.keys()) - set(self._allocated.keys()) - set(self._waiting.keys())

    def _attemptAllocationMethod(self, name, method):
        assert name not in self._waiting
        assert name not in self._allocated
        requirement = self._requirements[name]
        stateMachine = method(name, requirement)
        if stateMachine is None:
            return
        self._waiting[name] = stateMachine
        stateMachine.setDestroyCallback(self._stateMachineSelfDestructed)
        stateMachine.assign(
            stateChangeCallback=lambda x: self._stateMachineChangedState(name, stateMachine),
            imageLabel=requirement['imageLabel'],
            imageHint=requirement['imageHint'])

    def _stateMachineChangedState(self, name, stateMachine):
        if stateMachine.state() == hoststatemachine.STATE_INAUGURATION_DONE:
            assert name in self._waiting
            del self._waiting[name]
            self._allocated[name] = stateMachine
            if self.done():
                self._stateChangeCallback(self)

    def _stateMachineSelfDestructed(self, stateMachine):
        raise NotImplementedError("not implemented")
        self._hosts.destroy(stateMachine)
