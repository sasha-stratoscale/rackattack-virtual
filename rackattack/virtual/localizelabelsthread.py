import threading
import logging
from rackattack.virtual import sh
from rackattack.common import globallock


class LocalizeLabelsThread(threading.Thread):
    def __init__(self, labels, labelsLocalizedCallback, labelsLocalizationFailedCallback):
        self._labels = labels
        self._labelsLocalizedCallback = labelsLocalizedCallback
        self._labelsLocalizationFailedCallback = labelsLocalizationFailedCallback
        threading.Thread.__init__(self)
        self.daemon = True
        threading.Thread.start(self)

    def run(self):
        try:
            for label in self._labels:
                sh.run(["solvent", "localize", "--label", label])
        except Exception as e:
            logging.exception("Unable to localize label '%(label)s'", dict(label=label))
            with globallock.lock:
                self._labelsLocalizationFailedCallback(str(e))
        else:
            with globallock.lock:
                self._labelsLocalizedCallback()
