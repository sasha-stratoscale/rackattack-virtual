from rackattack.tcp import heartbeat
from rackattack.common import baseipcserver
from rackattack.virtual.kvm import network


class IPCServer(baseipcserver.BaseIPCServer):
    def __init__(self, allocations):
        self._allocations = allocations
        baseipcserver.BaseIPCServer.__init__(self)

    def cmd_allocate(self, requirements, allocationInfo):
        allocation = self._allocations.create(requirements)
        return allocation.index()

    def cmd_allocation__nodes(self, id):
        allocation = self._allocations.byIndex(id)
        if allocation.dead():
            raise Exception("Must not fetch nodes from a dead allocation")
        if not allocation.done():
            raise Exception("Must not fetch nodes from a not done allocation")
        result = {}
        for name, vm in allocation.vms().iteritems():
            result[name] = dict(
                id=vm.id(),
                primaryMACAddress=vm.primaryMACAddress(),
                secondaryMACAddress=vm.secondaryMACAddress(),
                ipAddress=vm.ipAddress(),
                netmask=network.NETMASK,
                inauguratorServerIP=network.GATEWAY_IP_ADDRESS,
                gateway=network.GATEWAY_IP_ADDRESS,
                osmosisServerIP=network.GATEWAY_IP_ADDRESS)
        return result

    def cmd_allocation__free(self, id):
        allocation = self._allocations.byIndex(id)
        allocation.free()

    def cmd_allocation__done(self, id):
        allocation = self._allocations.byIndex(id)
        return allocation.done()

    def cmd_allocation__dead(self, id):
        allocation = self._allocations.byIndex(id)
        return allocation.dead()

    def cmd_heartbeat(self, ids):
        for id in ids:
            allocation = self._allocations.byIndex(id)
            allocation.heartbeat()
        return heartbeat.HEARTBEAT_OK

    def cmd_node__rootSSHCredentials(self, allocationID, nodeID):
        allocation = self._allocations.byIndex(allocationID)
        for vm in allocation.vms().values():
            if vm.id() == nodeID:
                return vm.rootSSHCredentials()
        raise Exception("Node with id '%s' was not found in this allocation" % nodeID)
