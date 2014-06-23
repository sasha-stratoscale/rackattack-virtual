import os
from rackattack.virtual.kvm import config
from rackattack.common import globallock
from rackattack.virtual.kvm import imagecommands
import collections
import glob
import logging


_Image = collections.namedtuple("_Image", ["filename", "sizeGB", "imageHint"])


class FreeImagesPool:
    def __init__(self):
        self._pool = []
        self._index = 0
        self._allocated = 0
        self._findExistingImages()

    def put(self, filename, sizeGB, imageHint):
        assert self._allocated > 0
        newFilename = self._createFilename(sizeGB, imageHint)
        os.rename(filename, newFilename)
        self._pool.append(_Image(filename=newFilename, sizeGB=sizeGB, imageHint=imageHint))
        self._allocated -= 1

    def _createFilename(self, sizeGB, imageHint):
        assert globallock.assertLocked()
        self._index += 1
        return os.path.join(config.FREE_DISK_IMAGES_DIRECTORY, "%s__%dGB__%d.qcow2" % (
            imageHint, sizeGB, self._index))

    def get(self, sizeGB, imageHint):
        found = self._findFreeImage(sizeGB, imageHint)
        self._allocated += 1
        if found is None:
            newFilename = self._createFilename(sizeGB, imageHint)
            imagecommands.create(image=newFilename, sizeGB=sizeGB)
            self._deleteExcessiveImages()
            logging.info("Created new image '%(filename)s'", dict(filename=newFilename))
            return newFilename
        else:
            self._pool.remove(found)
            logging.info("Reusing existing image '%(filename)s'", dict(filename=found.filename))
            return found.filename

    def _deleteExcessiveImages(self):
        assert config.MAXIMUM_VMS <= config.MAXIMUM_DISK_IMAGES
        assert self._allocated <= config.MAXIMUM_VMS
        while self._allocated + len(self._pool) > config.MAXIMUM_DISK_IMAGES:
            image = self._pool.pop(0)
            logging.info("Too many disk images put aside. erasing '%(filename)s'", dict(
                filename=image.filename))
            os.unlink(image.filename)

    def _findFreeImage(self, sizeGB, imageHint):
        for image in self._pool:
            if image.sizeGB >= sizeGB and imageHint == imageHint:
                return image
        for image in self._pool:
            if image.sizeGB >= sizeGB:
                return image
        return None

    def _findExistingImages(self):
        for filename in glob.glob(config.FREE_DISK_IMAGES_DIRECTORY + "/*.qcow2"):
            fields = os.path.splitext(os.path.basename(filename))[0].split("__")
            imageHint = fields[0]
            sizeGB = int(fields[1][:-len("GB")])
            index = int(fields[2])
            self._index = max(self._index, index + 1)
            logging.info("Using '%(filename)s' as an existing image", dict(filename=filename))
            self._pool.append(_Image(filename=filename, sizeGB=sizeGB, imageHint=imageHint))
        self._deleteExcessiveImages()
