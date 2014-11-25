from twisted.web import resource
from twisted.web import static
import re
import shutil
import os
import datetime


class HTTPRootResource(resource.Resource):
    def __init__(self,
                 serialLogFilenameByNodeID,
                 createPostMortemPackForAllocationID,
                 managedPostMortemPacksDir):
        resource.Resource.__init__(self)
        self.putChild("host", _HostResource(serialLogFilenameByNodeID))
        self.putChild("allocation", _AllocationResource(
            createPostMortemPackForAllocationID, managedPostMortemPacksDir))


class _HostResource(resource.Resource):
    isLeaf = True

    def __init__(self, serialLogFilenameByNodeID):
        self._serialLogFilenameByNodeID = serialLogFilenameByNodeID
        resource.Resource.__init__(self)

    def render(self, request):
        match = re.search(r"/host/(.*)/serialLog", request.path)
        if match is None:
            raise Exception("Unknown path")
        filename = self._serialLogFilenameByNodeID(match.group(1))
        renderer = static.File(filename)
        return renderer.render(request)


class _AllocationResource(resource.Resource):
    isLeaf = True

    def __init__(self, createPostMortemPackForAllocationID, managedPostMortemPacksDir):
        self._createPostMortemPackForAllocationID = createPostMortemPackForAllocationID
        self._managedPostMortemPacksDir = managedPostMortemPacksDir
        resource.Resource.__init__(self)

    def render(self, request):
        match = re.search(r"/allocation/(.*)/postMortemPack", request.path)
        if match is None:
            raise Exception("Unknown path")
        filename = self._createPostMortemPackForAllocationID(match.group(1))
        managedFilename = self._createManagedFilename(match.group(1))
        shutil.move(filename, managedFilename)
        renderer = static.File(managedFilename)
        return renderer.render(request)

    def _createManagedFilename(self, id):
        if not os.path.isdir(self._managedPostMortemPacksDir):
            os.makedirs(self._managedPostMortemPacksDir)
        old = sorted(os.listdir(self._managedPostMortemPacksDir))
        MAXIMUM_OLD = 20
        if len(old) > MAXIMUM_OLD:
            for filename in old[:-MAXIMUM_OLD]:
                os.unlink(os.path.join(self._managedPostMortemPacksDir, filename))
        now = datetime.datetime.now()
        managedFilename = os.path.join(
            self._managedPostMortemPacksDir,
            "%d%02d%02d_%02d%02d%02d_%s" % (
                now.year, now.month, now.day, now.hour, now.minute, now.second, id))
        return managedFilename
