from rackattack.virtual.alloc import allocation
from rackattack.virtual.alloc import freepool
from rackattack.virtual.kvm import freeimagespool
from rackattack.common import globallock


class Allocations:
    def __init__(self, tftpboot, inaugurate, hosts, broadcaster):
        self._tftpboot = tftpboot
        self._inaugurate = inaugurate
        self._hosts = hosts
        self._broadcaster = broadcaster
        self._freePool = freepool.FreePool(hosts)
        self._freeImagesPool = freeimagespool.FreeImagesPool()
        self._allocations = []
        self._index = 1

    def create(self, requirements):
        assert globallock.assertLocked()
        alloc = allocation.Allocation(
            index=self._index, tftpboot=self._tftpboot, inaugurate=self._inaugurate,
            hosts=self._hosts, freePool=self._freePool, stateChangeCallback=self._allocationChangedState,
            requirements=requirements, freeImagesPool=self._freeImagesPool)
        self._allocations.append(alloc)
        self._index += 1
        return alloc

    def byIndex(self, index):
        assert globallock.assertLocked()
        for alloc in self._allocations:
            if alloc.index() == index:
                return alloc
        raise IndexError("No such allocation")

    def all(self):
        assert globallock.assertLocked()
        return self._allocations

    def _cleanup(self):
        self._allocations = [a for a in self._allocations is not a.deadForAWhile()]

    def _allocationChangedState(self, allocation):
        self._broadcaster.allocationChangedState(allocation.index())
