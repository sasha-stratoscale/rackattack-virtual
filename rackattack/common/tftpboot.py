import os
import shutil
import tempfile
import atexit
import logging


INAUGURATOR_KERNEL = "/usr/share/inaugurator/inaugurator.vmlinuz"
INAUGURATOR_INITRD = "/usr/share/inaugurator/inaugurator.thin.initrd.img"


class TFTPBoot:
    def __init__(
            self, netmask, inauguratorServerIP, inauguratorGatewayIP,
            osmosisServerIP, rootPassword, withLocalObjectStore):
        self._netmask = netmask
        self._inauguratorServerIP = inauguratorServerIP
        self._inauguratorGatewayIP = inauguratorGatewayIP
        self._osmosisServerIP = osmosisServerIP
        self._withLocalObjectStore = withLocalObjectStore
        self._root = tempfile.mkdtemp(suffix=".tftpboot")
        self._rootPassword = rootPassword
        atexit.register(self._cleanup)
        self._pxelinuxConfigDir = os.path.join(self._root, "pxelinux.cfg")
        self._installPXELinux()

    def root(self):
        return self._root

    def _cleanup(self):
        shutil.rmtree(self._root, ignore_errors=True)

    def _installPXELinux(self):
        if os.path.exists("/usr/share/syslinux/menu.c32"):
            shutil.copy("/usr/share/syslinux/menu.c32", self._root)
        else:
            shutil.copy("/usr/lib/syslinux/modules/bios/menu.c32", self._root)
            shutil.copy("/usr/lib/syslinux/modules/bios/ldlinux.c32", self._root)
            shutil.copy("/usr/lib/syslinux/modules/bios/libutil.c32", self._root)
        if os.path.exists("/usr/share/syslinux/pxelinux.0"):
            shutil.copy("/usr/share/syslinux/pxelinux.0", self._root)
        else:
            shutil.copy("/usr/lib/PXELINUX/pxelinux.0", self._root)
        shutil.copy(INAUGURATOR_KERNEL, self._root)
        shutil.copy(INAUGURATOR_INITRD, self._root)
        os.mkdir(self._pxelinuxConfigDir)

    def configureForInaugurator(self, mac, ip, clearDisk=False):
        if clearDisk:
            logging.info("Configuring host %(ipAddress)s inaugurator to clearDisk", dict(ipAddress=ip))
        self._writeConfiguration(mac, self._configurationForInaugurator(mac, ip, clearDisk=clearDisk))

    def configureForLocalBoot(self, mac):
        self._writeConfiguration(mac, _CONFIGURATION_FOR_LOCAL_BOOT)

    def _writeConfiguration(self, mac, contents):
        basename = '01-' + mac.replace(':', '-')
        path = os.path.join(self._pxelinuxConfigDir, basename)
        with open(path, "w") as f:
            f.write(contents)

    def _configurationForInaugurator(self, mac, ip, clearDisk):
        return _INAUGURATOR_TEMPLATE % dict(
            inauguratorCommandLine=self.inauguratorCommandLine(mac, ip, clearDisk),
            inauguratorKernel=os.path.basename(INAUGURATOR_KERNEL),
            inauguratorInitrd=os.path.basename(INAUGURATOR_INITRD))

    def inauguratorCommandLine(self, mac, ip, clearDisk):
        result = _INAUGURATOR_COMMAND_LINE % dict(
            macAddress=mac, ipAddress=ip, netmask=self._netmask,
            osmosisServerIP=self._osmosisServerIP, inauguratorServerIP=self._inauguratorServerIP,
            inauguratorGatewayIP=self._inauguratorGatewayIP,
            rootPassword=self._rootPassword)
        if self._withLocalObjectStore:
            result += " --inauguratorWithLocalObjectStore"
        if clearDisk:
            result += " --inauguratorClearDisk"
        return result


_INAUGURATOR_TEMPLATE = r"""
#serial support on port0 (COM1) running baud-rate 115200
SERIAL 0 115200
#VGA output parallel to serial disabled
CONSOLE 0

default menu.c32
prompt 0
timeout 1

menu title RackAttack PXE Boot Menu - Inaugurator

label Latest
    menu label Latest
    kernel %(inauguratorKernel)s
    initrd %(inauguratorInitrd)s
    append %(inauguratorCommandLine)s
"""

_CONFIGURATION_FOR_LOCAL_BOOT = """
#serial support on port0 (COM1) running baud-rate 115200
SERIAL 0 115200
#VGA output parallel to serial disabled
CONSOLE 0

default menu.c32
prompt 0
timeout 1

menu title RackAttack PXE Boot Menu - Local Disk

label BootFromLocalDisk
    menu label BootFromLocalDisk
    localboot 0
"""

_INAUGURATOR_COMMAND_LINE = \
    "console=ttyS0,115200n8 " \
    "--inauguratorSource=network " \
    "--inauguratorUseNICWithMAC=%(macAddress)s --inauguratorOsmosisObjectStores=%(osmosisServerIP)s:1010 " \
    "--inauguratorServerHostname=%(inauguratorServerIP)s --inauguratorIPAddress=%(ipAddress)s " \
    "--inauguratorNetmask=%(netmask)s --inauguratorGateway=%(inauguratorGatewayIP)s " \
    "--inauguratorChangeRootPassword=%(rootPassword)s"
