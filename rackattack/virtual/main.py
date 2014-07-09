import logging
logging.basicConfig(level=logging.DEBUG)
from rackattack.ssh import connection
connection.discardParamikoLogs()
connection.discardSSHDebugMessages()
import time
import argparse
from rackattack.virtual import ipcserver
from rackattack.virtual import buildimagethread
from rackattack.virtual.kvm import cleanup
import rackattack.virtual.handlekill
from rackattack.virtual.kvm import config
from rackattack.virtual.kvm import network
from rackattack.virtual.kvm import imagestore
from rackattack.common import dnsmasq
from rackattack.common import tftpboot
from rackattack.common import inaugurate
from rackattack.common import timer
from rackattack.virtual.alloc import allocations
from rackattack.tcp import publish
import atexit

parser = argparse.ArgumentParser()
parser.add_argument("--requestPort", default=1014, type=int)
parser.add_argument("--subscribePort", default=1015, type=int)
parser.add_argument("--maximumVMs", type=int)
parser.add_argument("--diskImagesDirectory")
parser.add_argument("--serialLogsDirectory")
args = parser.parse_args()

if args.maximumVMs:
    config.MAXIMUM_VMS = args.maximumVMs
if args.diskImagesDirectory:
    config.DISK_IMAGES_DIRECTORY = args.diskImagesDirectory
if args.serialLogsDirectory:
    config.SERIAL_LOGS_DIRECTORY = args.serialLogsDirectory

cleanup.cleanup()
atexit.register(cleanup.cleanup)
timer.TimersThread()
network.setUp()
tftpbootInstance = tftpboot.TFTPBoot(
    netmask=network.NETMASK,
    inauguratorServerIP=network.GATEWAY_IP_ADDRESS,
    osmosisServerIP=network.GATEWAY_IP_ADDRESS,
    rootPassword=config.ROOT_PASSWORD)
dnsmasqInstance = dnsmasq.DNSMasq(
    tftpboot=tftpbootInstance,
    serverIP=network.GATEWAY_IP_ADDRESS,
    netmask=network.NETMASK,
    firstIP=network.FIRST_IP,
    lastIP=network.LAST_IP,
    gateway=network.GATEWAY_IP_ADDRESS,
    nameserver=network.GATEWAY_IP_ADDRESS)
for mac, ip in network.allNodesMACIPPairs():
    dnsmasqInstance.add(mac, ip)
inaugurateInstance = inaugurate.Inaugurate(bindHostname=network.GATEWAY_IP_ADDRESS)
imageStore = imagestore.ImageStore()
buildImageThread = buildimagethread.BuildImageThread(
    inaugurate=inaugurateInstance, tftpboot=tftpbootInstance, imageStore=imageStore)
publishInstance = publish.Publish(tcpPort=args.subscribePort)
allVMs = dict()
allocationsInstance = allocations.Allocations(
    broadcaster=publishInstance, buildImageThread=buildImageThread,
    imageStore=imageStore, allVMs=allVMs)
server = ipcserver.IPCServer(tcpPort=args.requestPort, allocations=allocationsInstance)
logging.info("Virtual RackAttack up and running")
while True:
    time.sleep(1000 * 1000)
