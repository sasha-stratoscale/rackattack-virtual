import unittest
from rackattack.common import hoststatemachine
from rackattack.common import globallock
from rackattack.common import timer
from rackattack.common import hosts
from rackattack.virtual.kvm import vm
from rackattack.virtual.kvm import config
from rackattack.virtual.alloc import allocations
from rackattack.virtual.alloc import freepool
from rackattack.virtual import localizelabelsthread


class Empty:
    pass


class FakeStateMachine:
    def __init__(self, hostImplementation):
        self._hostImplementation = hostImplementation

    def hostImplementation(self):
        return self._hostImplementation

    def imageHint(self):
        return self._imageHint

    def assign(self, stateChangeCallback, imageLabel, imageHint):
        self._assigned = True
        self._stateChangeCallback = stateChangeCallback
        self._imageLabel = imageLabel
        self._imageHint = imageHint

    def unassign(self):
        self._assigned = False

    def setDestroyCallback(self, callback):
        self._destroyCallback = callback

    def state(self):
        return self._state

    def destroy(self):
        self._destroyed = True


class Test(unittest.TestCase):
    def setUp(self):
        config.MAXIMUM_VMS = 4
        globallock.lock.acquire()
        timer.scheduleIn = self.scheduleTimerIn
        timer.scheduleAt = self.scheduleTimerAt
        timer.cancelAllByTag = self.cancelAllTimersByTag
        freepool.time = Empty()
        freepool.time.time = self.getTime
        self.time = 1000000
        self.timers = []
        vm.VM = Empty()
        vm.VM.create = self.createVM
        hoststatemachine.HostStateMachine = self.constructStateMachine
        self.fakeInaugurate = "fake inaugurate"
        self.fakeTFTPBoot = "fake tftpboot"
        self.fakeBroadcaster = Empty()
        self.fakeBroadcaster.allocationChangedState = self.broadcastAllocationChangedState
        self.stateMachines = []
        localizelabelsthread.LocalizeLabelsThread = self.createLocalizeLabelsThread
        self.expectedLocalizeLabels = None

        self.expectedVMCreateIndex = None
        self.expectedVMCreateRequirement = None
        self.expectedAllocationChangedStateBroadcast = None
        self.construct()

    def tearDown(self):
        globallock.lock.release()

    def construct(self):
        self.testedHosts = hosts.Hosts()
        self.testedAllocations = allocations.Allocations(
            tftpboot=self.fakeTFTPBoot, inaugurate=self.fakeInaugurate, hosts=self.testedHosts,
            broadcaster=self.fakeBroadcaster)

    def getTime(self):
        return self.time

    def scheduleTimerIn(self, timeout, callback, tag):
        self._scheduleTimer(callback, tag)

    def scheduleTimerAt(self, when, callback, tag):
        self._scheduleTimer(callback, tag)

    def _scheduleTimer(self, callback, tag):
        for existingTimer in self.timers:
            self.assertIsNot(existingTimer['tag'], tag)
        self.timers.append(dict(callback=callback, tag=tag))

    def cancelAllTimersByTag(self, tag):
        for existingTimer in list(self.timers):
            if existingTimer['tag'] is tag:
                self.timers.remove(existingTimer)

    def triggerTimeout(self):
        self.assertIsNot(self.currentTimer, None)
        self.assertIsNot(self.currentTimerTag, None)
        self.currentTimer()
        self.currentTimer = None
        self.currentTimerTag = None

    def createVM(self, index, requirement, freeImagesPool):
        self.assertEquals(index, self.expectedVMCreateIndex)
        self.expectedVMCreateIndex = None
        self.assertEquals(requirement, self.expectedVMCreateRequirement)
        self.expectedVMCreateRequirement = None
        result = Empty()
        result._index = index
        result.index = lambda: index
        result._requirement = requirement
        result.fulfillsRequirement = lambda r: r == result._requirement
        self.expectedHostImplementationInStateMachineConstruction = result
        return result

    def createLocalizeLabelsThread(self, labels, labelsLocalizedCallback, labelsLocalizationFailedCallback):
        self.assertEquals(labels, self.expectedLocalizeLabels)
        self.labelsLocalizedCallback = labelsLocalizedCallback
        self.labelsLocalizationFailedCallback = labelsLocalizationFailedCallback

    def constructStateMachine(self, hostImplementation, inaugurate, tftpboot):
        self.assertIs(hostImplementation, self.expectedHostImplementationInStateMachineConstruction)
        self.expectedHostImplementationInStateMachineConstruction = None
        self.assertIs(inaugurate, self.fakeInaugurate)
        self.assertIs(tftpboot, self.fakeTFTPBoot)
        result = FakeStateMachine(hostImplementation)
        self.stateMachines.append(result)
        return result

    def broadcastAllocationChangedState(self, allocationIndex):
        self.assertEquals(allocationIndex, self.expectedAllocationChangedStateBroadcast)
        self.expectedAllocationChangedStateBroadcast = None

    def singleRequirement(self):
        return dict(name=dict(
            imageLabel="image label", imageHint="image hint",
            hardwareConstraints="fake hardware constraints"))

    def test_AllocateOne(self):
        self.expectedVMCreateIndex = 1
        self.expectedVMCreateRequirement = self.singleRequirement()['name']
        self.expectedLocalizeLabels = set(["image label"])
        allocation = self.testedAllocations.create(self.singleRequirement())
        self.assertFalse(allocation.done())
        self.assertFalse(allocation.dead())
        self.assertFalse(allocation.deadForAWhile())
        self.assertIs(self.testedAllocations.byIndex(allocation.index()), allocation)
        self.assertEquals(len(self.stateMachines), 0)

        self.labelsLocalizedCallback()
        self.labelsLocalizedCallback = None
        self.assertEquals(len(self.stateMachines), 1)
        self.assertEquals(self.stateMachines[0]._imageLabel, "image label")
        self.assertEquals(self.stateMachines[0]._imageHint, "image hint")
        self.assertEquals(self.stateMachines[0]._hostImplementation._index, 1)
        self.assertIsNot(self.stateMachines[0]._stateChangeCallback, None)
        self.assertTrue(self.stateMachines[0]._assigned)

        self.stateMachines[0]._state = hoststatemachine.STATE_QUICK_RECLAIMATION_IN_PROGRESS
        self.stateMachines[0]._stateChangeCallback(self.stateMachines[0])
        self.assertFalse(allocation.done())

        self.stateMachines[0]._state = hoststatemachine.STATE_SLOW_RECLAIMATION_IN_PROGRESS
        self.stateMachines[0]._stateChangeCallback(self.stateMachines[0])
        self.assertFalse(allocation.done())

        self.stateMachines[0]._state = hoststatemachine.STATE_CHECKED_IN
        self.stateMachines[0]._stateChangeCallback(self.stateMachines[0])
        self.assertFalse(allocation.done())

        self.stateMachines[0]._state = hoststatemachine.STATE_INAUGURATION_LABEL_PROVIDED
        self.stateMachines[0]._stateChangeCallback(self.stateMachines[0])
        self.assertFalse(allocation.done())

        self.expectedAllocationChangedStateBroadcast = 1
        self.stateMachines[0]._state = hoststatemachine.STATE_INAUGURATION_DONE
        self.stateMachines[0]._stateChangeCallback(self.stateMachines[0])
        self.assertTrue(allocation.done())
        self.assertIs(self.expectedAllocationChangedStateBroadcast, None)
        self.assertFalse(allocation.dead())
        self.assertFalse(allocation.deadForAWhile())

    def allocateOneAndFree(self):
        self.expectedVMCreateIndex = 1
        self.expectedVMCreateRequirement = self.singleRequirement()['name']
        self.expectedLocalizeLabels = set(["image label"])
        allocation = self.testedAllocations.create(self.singleRequirement())
        self.labelsLocalizedCallback()
        self.labelsLocalizedCallback = None
        self.assertFalse(allocation.done())
        self.expectedAllocationChangedStateBroadcast = 1
        self.stateMachines[0]._state = hoststatemachine.STATE_INAUGURATION_DONE
        self.stateMachines[0]._stateChangeCallback(self.stateMachines[0])
        self.assertTrue(allocation.done())
        self.assertIs(self.expectedAllocationChangedStateBroadcast, None)

        self.expectedAllocationChangedStateBroadcast = 1
        allocation.free()
        self.assertTrue(allocation.dead())
        self.assertFalse(allocation.deadForAWhile())
        self.assertIs(self.expectedAllocationChangedStateBroadcast, None)

    def test_Allocate_Free_UnusedAndDestroyed(self):
        self.allocateOneAndFree()

        self.assertEquals(len(self.timers), 1)
        self.time += 60 * 60
        self.timers[0]['callback']()
        self.assertFalse(self.stateMachines[0]._assigned)
        self.assertTrue(self.stateMachines[0]._destroyed)

    def test_Allocate_Free_Reuse(self):
        self.allocateOneAndFree()
        self.expectedVMCreateIndex = 2
        self.expectedVMCreateRequirement = self.singleRequirement()['name']
        allocation = self.testedAllocations.create(self.singleRequirement())
        self.labelsLocalizedCallback()
        self.labelsLocalizedCallback = None
        self.assertFalse(allocation.done())
        self.expectedAllocationChangedStateBroadcast = 2
        self.assertEquals(len(self.stateMachines), 1)
        self.stateMachines[0]._state = hoststatemachine.STATE_INAUGURATION_DONE
        self.stateMachines[0]._stateChangeCallback(self.stateMachines[0])
        self.assertTrue(allocation.done())
        self.assertIs(self.expectedAllocationChangedStateBroadcast, None)

        self.expectedAllocationChangedStateBroadcast = 2
        allocation.free()
        self.assertTrue(allocation.dead())
        self.assertFalse(allocation.deadForAWhile())
        self.assertIs(self.expectedAllocationChangedStateBroadcast, None)


if __name__ == '__main__':
    unittest.main()
