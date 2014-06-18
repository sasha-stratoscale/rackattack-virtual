from rackattack.virtual.kvm import vm
from rackattack.virtual.kvm import config
from rackattack.common import hoststatemachine
import logging


class Acumulate:
    def __init__(self, tftpboot, inaugurate, hosts, freePool):
        self._tftpboot = tftpboot
        self._inaugurate = inaugurate
        self._hosts = hosts
        self._freePool = freePool
        self._acumulated = dict()

    def acumulated(self):
        return self._acumulated

    def free(self):
        for stateMachine in self._acumulated.values():
            stateMachine.unassign()
            stateMachine.setDestroyCallback(None)
            self._freePool.put(stateMachine)
        self._acumulated = None

    def tryAllocateFromFreePoolWithHint(self, name, requirement):
        for stateMachine in list(self._freePool.all()):
            if stateMachine.imageHint() == requirement['imageHint']:
                if stateMachine.hostImplementation().fulfillsRequirement(requirement):
                    self._allocateFromFreePool(name, stateMachine, requirement)
                    return stateMachine
        return None

    def tryAllocateFromFreePool(self, name, requirement):
        for stateMachine in list(self._freePool.all()):
            if stateMachine.hostImplementation().fulfillsRequirement(requirement):
                self._allocateFromFreePool(name, stateMachine, requirement)
                return stateMachine
        return None

    def tryCreate(self, name, requirement):
        if not self._createAllowed():
            return None
        try:
            assert name not in self._acumulated
            vmInstance = vm.VM.create(self._hosts.availableIndex(), requirement)
            try:
                stateMachine = hoststatemachine.HostStateMachine(
                    hostImplementation=vmInstance, inaugurate=self._inaugurate, tftpboot=self._tftpboot)
            except:
                vmInstance.destroy()
                raise
            self._hosts.add(stateMachine)
            self._acumulated[name] = stateMachine
            return stateMachine
        except:
            logging.exception("Unable to create a new VM")
            return None

    def tryDestroyFromFreePoolAndCreate(self, name, requirement):
        if len(list(self._freePool.all())) == 0:
            return None
        toDestroy = self._freePool.takeOut(list(self._freePool.all())[0])
        self._hosts.destroy(toDestroy)
        return self._tryCreate()

    def _allocateFromFreePool(self, name, stateMachine, requirement):
        self._freePool.takeOut(stateMachine)
        assert name not in self._acumulated
        self._acumulated[name] = stateMachine

    def _createAllowed(self):
        return len(self._hosts.all()) < config.MAXIMUM_VMS
