from rackattack.virtual.kvm import libvirtsingleton
from rackattack.virtual.kvm import config
import logging
import os
import glob


def _cleanupDomains():
    logging.info("Cleaning up previous rackattack nodes")
    cleaned = 0
    ignored = 0
    with libvirtsingleton.it().lock():
        libvirt = libvirtsingleton.it().libvirt()
        for domain in libvirt.listAllDomains(0xFF):
            if not domain.name().startswith(config.DOMAIN_PREFIX):
                ignored += 1
                continue
            if domain.isActive():
                domain.destroy()
            domain.undefine()
            cleaned += 1
    logging.info(
        "Done cleaning up previous rackattack nodes. %(cleaned)d cleaned, "
        "%(ignored)d ignored", dict(cleaned=cleaned, ignored=ignored))


def _cleanupDiskImages():
    logging.info("Cleaning up previous disk images")
    for filename in glob.glob(config.DISK_IMAGES_DIRECTORY + "/*.qcow2"):
        os.unlink(filename)


def cleanup():
    _cleanupDomains()
    _cleanupDiskImages()
