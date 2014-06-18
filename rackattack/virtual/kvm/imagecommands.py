import os
from rackattack.virtual import sh


def create(image, sizeGB):
    dirname = os.path.dirname(image)
    if not os.path.isdir(dirname):
        os.makedirs(dirname, 0777)
    sh.run(['qemu-img', 'create', '-f', 'qcow2', image, '%dG' % sizeGB])
    os.chmod(image, 0666)
