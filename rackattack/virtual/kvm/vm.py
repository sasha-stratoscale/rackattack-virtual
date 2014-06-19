from rackattack.virtual.kvm import manifest
from rackattack.virtual.kvm import libvirtsingleton
from rackattack.virtual.kvm import config
from rackattack.virtual.kvm import network
from rackattack.virtual.kvm import imagecommands
import os


class VM:
    def __init__(
            self, index, requirement, freeImagesPool, domain,
            manifest, disk1SizeGB, disk2SizeGB):
        self._index = index
        self._requirement = requirement
        self._freeImagesPool = freeImagesPool
        self._domain = domain
        self._manifest = manifest
        self._disk1SizeGB = disk1SizeGB
        self._disk2SizeGB = disk2SizeGB

    def index(self):
        return self._index

    def id(self):
        return self._nameFromIndex(self._index)

    def primaryMACAddress(self):
        return network.primaryMACAddressFromVMIndex(self._index)

    def secondaryMACAddress(self):
        return network.secondMACAddressFromVMIndex(self._index)

    def ipAddress(self):
        return network.ipAddressFromVMIndex(self._index)

    def rootSSHCredentials(self):
        return dict(hostname=self.ipAddress(), username="root", password=config.ROOT_PASSWORD)

    def coldRestart(self):
        with libvirtsingleton.it().lock():
            self._domain.destroy()
            self._domain.create()

    def destroy(self):
        with libvirtsingleton.it().lock():
            self._domain.destroy()
            self._domain.undefine()
        self._freeImagesPool.put(
            filename=self._manifest.disk1Image(), sizeGB=self._manifest.disk1SizeGB(),
            imageHint=self._requirement['imageHint'])
        os.unlink(self._manifest.disk2Image())

    def fulfillsRequirement(self, requirement):
        hardwareConstraints = requirement['hardwareConstraints']
        return self._manifest.vcpus() >= hardwareConstraints['minimumCPUs'] and \
            self._manifest.memoryMB() >= hardwareConstraints['minimumRAMGB'] * 1024 and \
            self._disk1SizeGB >= hardwareConstraints['minimumDisk1SizeGB'] and \
            self._disk2SizeGB >= hardwareConstraints['minimumDisk2SizeGB']

    @classmethod
    def create(cls, index, requirement, freeImagesPool):
        name = cls._nameFromIndex(index)
        image1 = os.path.join(config.DISK_IMAGES_DIRECTORY, name + "_disk1.qcow2")
        image2 = os.path.join(config.DISK_IMAGES_DIRECTORY, name + "_disk2.qcow2")
        serialLog = os.path.join(config.SERIAL_LOGS_DIRECTORY, name + ".serial.txt")
        if not os.path.isdir(os.path.dirname(serialLog)):
            os.makedirs(os.path.dirname(serialLog))
        hardwareConstraints = requirement['hardwareConstraints']
        previousFilename = freeImagesPool.get(
            sizeGB=hardwareConstraints['minimumDisk1SizeGB'], imageHint=requirement['imageHint'])
        os.rename(previousFilename, image1)
        imagecommands.create(
            image=image2, sizeGB=hardwareConstraints['minimumDisk2SizeGB'])
        mani = manifest.Manifest.create(
            name=name,
            memoryMB=int(1024 * hardwareConstraints['minimumRAMGB']),
            vcpus=hardwareConstraints['minimumCPUs'],
            disk1Image=image1,
            disk2Image=image2,
            primaryMACAddress=network.primaryMACAddressFromVMIndex(index),
            secondaryMACAddress=network.secondMACAddressFromVMIndex(index),
            networkName=network.NAME,
            serialOutputFilename=serialLog)
        with libvirtsingleton.it().lock():
            domain = libvirtsingleton.it().libvirt().defineXML(mani.xml())
            domain.create()
        return cls(
            index=index, domain=domain,
            requirement=requirement, freeImagesPool=freeImagesPool,
            manifest=mani,
            disk1SizeGB=hardwareConstraints['minimumDisk1SizeGB'],
            disk2SizeGB=hardwareConstraints['minimumDisk2SizeGB'])

    @classmethod
    def _nameFromIndex(cls, index):
        return "rackattack-vm%d" % index
