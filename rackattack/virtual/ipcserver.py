import threading
import logging
import simplejson
from rackattack.tcp import heartbeat
from rackattack.tcp import suicide
from rackattack.tcp import debug
from rackattack import api
from rackattack.common import globallock
from rackattack.virtual.kvm import network
import Queue


class IPCServer(threading.Thread):
    def __init__(self, allocations):
        self._allocations = allocations
        self._queue = Queue.Queue()
        threading.Thread.__init__(self)
        self.daemon = True
        threading.Thread.start(self)

    def _cmd_handshake(self, versionInfo):
        if versionInfo['RACKATTACK_VERSION'] != api.VERSION:
            raise Exception(
                "Rackattack API version on the client side is '%s', and '%s' on the provider" % (
                    versionInfo['RACKATTACK_VERSION'], api.VERSION))

    def _cmd_allocate(self, requirements, allocationInfo):
        allocation = self._allocations.create(requirements)
        return allocation.index()

    def _cmd_allocation__nodes(self, id):
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

    def _cmd_allocation__free(self, id):
        allocation = self._allocations.byIndex(id)
        allocation.free()

    def _cmd_allocation__done(self, id):
        allocation = self._allocations.byIndex(id)
        return allocation.done()

    def _cmd_allocation__dead(self, id):
        allocation = self._allocations.byIndex(id)
        return allocation.dead()

    def _cmd_heartbeat(self, ids):
        for id in ids:
            allocation = self._allocations.byIndex(id)
            allocation.heartbeat()
        return heartbeat.HEARTBEAT_OK

    def _cmd_node__rootSSHCredentials(self, allocationID, nodeID):
        allocation = self._allocations.byIndex(allocationID)
        for vm in allocation.vms().values():
            if vm.id() == nodeID:
                return vm.rootSSHCredentials()
        raise Exception("Node with id '%s' was not found in this allocation" % nodeID)

    def run(self):
        try:
            while True:
                try:
                    self._work()
                except:
                    logging.exception("Handling")
        except:
            logging.exception("Virtual IPC server aborts")
            suicide.killSelf()
            raise

    def handle(self, string, respondCallback):
        try:
            incoming = simplejson.loads(string)
            if incoming['cmd'] == 'handshake':
                with debug.logNetwork("Handling handshake"):
                    response = self._cmd_handshake(** incoming['arguments'])
                    respondCallback(simplejson.dumps(response))
            else:
                transaction = debug.Transaction("Handling: %s" % incoming['cmd'])
                self._queue.put((incoming, respondCallback, transaction))
        except Exception, e:
            logging.exception('Handling')
            response = dict(exceptionString=str(e), exceptionType=e.__class__.__name__)
            respondCallback(simplejson.dumps(response))

    def _work(self):
        incoming, respondCallback, transaction = self._queue.get()
        transaction.reportState('dequeued (%d left in queue)' % self._queue.qsize())
        try:
            handler = getattr(self, "_cmd_" + incoming['cmd'])
            with globallock.lock():
                response = handler(** incoming['arguments'])
        except Exception, e:
            logging.exception('Handling')
            response = dict(exceptionString=str(e), exceptionType=e.__class__.__name__)
        transaction.finished()
        respondCallback(simplejson.dumps(response))
