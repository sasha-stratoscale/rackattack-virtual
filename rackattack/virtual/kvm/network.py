from rackattack.virtual.kvm import libvirtsingleton
import logging
import subprocess
import re

NAME = "rackattacknet"
_IP_ADDRESS_FORMAT = "192.168.124.%d"
GATEWAY_IP_ADDRESS = _IP_ADDRESS_FORMAT % 1
NETMASK = '255.255.255.0'


def ipAddressFromVMIndex(index):
    return _IP_ADDRESS_FORMAT % (10 + index)


FIRST_IP = ipAddressFromVMIndex(0)
LAST_IP = ipAddressFromVMIndex(100)


def primaryMACAddressFromVMIndex(index):
    assert index < (1 << 16)
    return "52:54:00:00:%02X:%02X" % (int(index / 256), index % 256)


def secondMACAddressFromVMIndex(index):
    assert index < (1 << 16)
    return "52:54:00:01:%02X:%02X" % (int(index / 256), index % 256)


def allNodesMACIPPairs():
    return [(primaryMACAddressFromVMIndex(i), ipAddressFromVMIndex(i)) for i in xrange(100)]


def setUp():
    with libvirtsingleton.it().lock():
        libvirt = libvirtsingleton.it().libvirt()
        try:
            libvirt.networkLookupByName(NAME)
            logging.info("Libvirt network is already set up")
        except:
            _create(libvirt)
            logging.info("Libvirt network created")
    _openFirewall()


def _openFirewall():
    if not _firewallOpen():
        subprocess.check_call(["iptables", "-I", "INPUT", "-i", _BRIDGE_NAME, "-j", "ACCEPT"])
        assert _firewallOpen()


def _firewallOpen():
    inputChain = subprocess.check_output(["iptables", '--list', 'INPUT', '-v'])
    expression = r"\n\s*\w+\s+\w+\s+ACCEPT\s+all\s+--\s+%s\s+any\s+anywhere\s+anywhere\s*\n" % _BRIDGE_NAME
    return re.search(expression, inputChain) is not None


_BRIDGE_NAME = "rackattacknetbr"
_IP_ADDRESS_FORMAT = "192.168.124.%d"
_GATEWAY_IP_ADDRESS = _IP_ADDRESS_FORMAT % 1
_XML = """
<network>
  <name>%(name)s</name>
  <forward mode='nat'/>
  <bridge name='%(bridgeName)s' stp='on' delay='0' />
  <ip address='%(gatewayIPAddress)s' netmask='%(netmask)s'>
  </ip>
</network>
""" % dict(
    name=NAME, bridgeName=_BRIDGE_NAME,
    gatewayIPAddress=GATEWAY_IP_ADDRESS,
    netmask=NETMASK)


def _create(libvirt):
    libvirt.networkCreateXML(_XML)
