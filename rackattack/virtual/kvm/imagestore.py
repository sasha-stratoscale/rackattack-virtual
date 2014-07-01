import os
from rackattack.virtual.kvm import config
from rackattack.common import globallock
import glob
import logging
import json
import time


class ImageStore:
    def __init__(self):
        self._images = dict()
        self._findExistingImages()
        self._deleteExcessiveImages()

    def put(self, filename, imageLabel, sizeGB):
        assert (imageLabel, sizeGB) not in self._images
        newFilename = self._filename(imageLabel, sizeGB)
        if not os.path.isdir(os.path.dirname(newFilename)):
            os.makedirs(os.path.dirname(newFilename))
        os.rename(filename, newFilename)
        self._images[(imageLabel, sizeGB)] = newFilename

    def _filename(self, imageLabel, sizeGB):
        assert globallock.assertLocked()
        return os.path.join(config.IMAGE_STORE_DIRECTORY, "%s____%dGB.qcow2" % (imageLabel, sizeGB))

    def get(self, imageLabel, sizeGB):
        if (imageLabel, sizeGB) not in self._images:
            raise Exception("No such built image: '%s'/%dGB" % (imageLabel, sizeGB))
        lastUsed = self._lastUsed()
        lastUsed["%s____%d" % (imageLabel, sizeGB)] = time.time()
        with open(config.IMAGE_STORE_LAST_USED, "w") as f:
            json.dump(lastUsed, f)
        return self._images[(imageLabel, sizeGB)]

    def _deleteExcessiveImages(self):
        lastUsed = self._lastUsed()
        timeout = time.time() - config.ERASE_IF_IMAGE_UNUSED_FOR
        for label, sizeGB in dict(self._images):
            if lastUsed.get("%s____%d" % (label, sizeGB), time.time()) < timeout:
                logging.info("Label '%(label)s' %(sizeGB)GB unused for too long. Erasing", dict(
                    label=label, sizeGB=sizeGB))
                os.unlink(self._images[(label, sizeGB)])
                del self._images[(label, sizeGB)]

    def _findExistingImages(self):
        for filename in glob.glob(config.IMAGE_STORE_DIRECTORY + "/*.qcow2"):
            fields = os.path.splitext(os.path.basename(filename))[0].split("____")
            imageLabel = fields[0]
            sizeGB = int(fields[1][:-len("GB")])
            logging.info("Using '%(filename)s' as an existing image", dict(filename=filename))
            self._images[(imageLabel, sizeGB)] = filename

    def _lastUsed(self):
        if os.path.exists(config.IMAGE_STORE_LAST_USED):
            with open(config.IMAGE_STORE_LAST_USED) as f:
                return json.load(f)
        else:
            return dict()
