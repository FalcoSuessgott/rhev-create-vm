#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Commandline utility for the creation of virtual machines
#
#    Autor:         tom.morelly@gmx.de
#    Date:          01.02.2019
#

import os
import sys
import ConfigParser
import argparse
import getpass
import json
import time
from terminaltables import AsciiTable, DoubleTable, SingleTable
import ovirtsdk4 as sdk
import ovirtsdk4.types as types

def parseArgs():
        """ Argument parser """
    parser = argparse.ArgumentParser()

        # Config
        parser.add_argument("-c", "--config", dest="configfile",action="store",
            help="Path to configfile. Use -m to print sample config file."
                + "\nDefault location is /etc/loadbalancer.conf.")
    # Password
    parser.add_argument("-p", "--password",action="store",
            help="password"),

        parser = parser.parse_args()

    # No Arguments
    if len(sys.argv) == 1:
            print "No arguments were specified. Please use -h option for more information.\nExiting."
                sys.exit(1)

    # Force Sudo
    if not os.getuid() == 0:
            print "ERROR: must be root to execute.\nExiting."
                sys.exit(1)

    # Verify config file
    if not os.path.isfile(parser.configfile):
            print "Configfile \"%s\" does not exist.\nExiting." % parser.configfile
                sys.exit(1)

    # Read config
    configHandler(parser.configfile)

    # Auth
    if not parser.password:
        password = getpass.getpass()
        session = connectToAPI(password)
    else:
        session = connectToAPI(parser.password)

    # List VMs
    createVM(session)

    # Add NICs
    addNICs(session)

    # Add disk
    addDisks(session)

    # boot over network
    startVMOverNetwork(session)

    # information
    printInformation(session)

def configHandler(configfile):
    """ Returns the config file handler """
    global configFile
    with open(configfile) as f:
                configFile = json.load(f)

def connectToAPI(password):
    """ Connects to rest api, returns key handler """
    url    = "https://"+configFile['rhevm']+"/ovirt-engine/api"
    ca    = configFile['ca_file']
    profile = configFile['profile']
    user    = os.environ['SUDO_USER']

    try:

        print "=================[ AUTHENTICATING TO RHEVM ]================="
         connection = sdk.Connection(
                    url=str(url),
                    username=str(user)+"@"+str(profile),
                    password=str(password),
                    ca_file=str(ca),
                debug=True)

        print ("Connecting to \"%s\" as \"%s@%s\"." % (url,user,profile))
        return connection
    except Exception as e:
        print str(e)
        sys.exit(1)


def createVM(session):
    """ Creates a virtual maschine """

    print "\n\n=================[ CREATING VMS ]================="

    try:
        for vm in configFile['vms']:
            hostname    = vm['hostname']
            cluster        = vm['cluster']
            template    = vm['template']
            memory        = vm['memory']

            vmService = session.system_service().vms_service()
                    vm = vmService.add(
                            types.Vm(
                                    name=hostname,
                                    memory = memory * 2**30,
                                    cluster=types.Cluster(
                                            name=cluster),
                                    template=types.Template(
                                            name=template),
                                    os=types.OperatingSystem(
                                            boot=types.Boot(
                                                    devices=[types.BootDevice.HD])),
                                    )
                            )
            print ("Created VM \"%s\" on cluster \"%s\" with template \"%s\"." % (hostname, cluster, template))
    except Exception as e:
        print str(e)
        sys.exit(1)

def addNICs(session):
    """ Adds NICs to an existing VM """

    print "\n\n=================[ ADDING NICS ]================="

        for vm in configFile['vms']:
                hostname        = vm['hostname']
                cluster         = vm['cluster']
                for nic in vm['interfaces']:
                        network = vm['interfaces'][nic]
                        profileId = None
                        profileName = None

                        systemService   = session.system_service()
                        vmService       = systemService.vms_service()
                        machine         = vmService.list(search='name=%s' % str(hostname))[0]
                        dcService       = session.system_service().data_centers_service()
                        dc              = dcService.list(search='Clusters.name=%s' % str(cluster))[0]
                        networkService  = dcService.service(dc.id).networks_service()

            # logical networks in respective cluster
                        for net in networkService.list():
                if net.name == str(network):
                    # logical network if of specified nic network in configfile
                    profileService = session.system_service().vnic_profiles_service()
                                for profile in profileService.list():
                        if profile.name == str(network):
                            try:
                                nicService = vmService.vm_service(machine.id).nics_service()
                                                    nicService.add(
                                                            types.Nic(
                                                            name=nic,
                                                            vnic_profile=types.VnicProfile(
                                                                id=profile.id),
                                                            ),
                                                    )
                                print "Adding logical network \"%s\" to \"%s\" as NIC \"%s\"." % (str(network), hostname, nic)
                            except Exception as e:
                                pass

def addDisks(session):
    """ Adds a disk to the virtual machine"""

    print "\n\n=================[ ADDING DISK ]================="

    for vm in configFile['vms']:
                hostname    = vm['hostname']
        vmService     = session.system_service().vms_service()
        machine     = vmService.list(search='name=%s' % str(hostname))[0]
        diskAttachmentsService = vmService.vm_service(machine.id).disk_attachments_service()

        for disk in vm['disks']:
            diskSize     = vm['disks'][disk]
            storageDomain     = vm['storage-domain']

            diskAttachment     = diskAttachmentsService.add(
                 types.DiskAttachment(
                    disk=types.Disk(
                        name=disk,
                        format=types.DiskFormat.COW,
                        provisioned_size=diskSize * 2**30,
                        storage_domains=[
                            types.StorageDomain(
                                name=storageDomain),
                        ],
                    ),
                    interface=types.DiskInterface.VIRTIO,
                    bootable=False,
                    active=True,
                    )
            )

            disksService    = session.system_service().disks_service()
            diskService     = disksService.disk_service(diskAttachment.disk.id)

            print "Adding Disk \"%s\" with %s Gb to \"%s\"." % (disk, diskSize, hostname)
            print "\tWaiting for Disk to come up..."

            while True:
                time.sleep(5)
                disk = diskService.get()
                if disk.status == types.DiskStatus.OK:
                    print "\tDisk ready."
                    break

def startVMOverNetwork(session):
    """ Starts created virtual machines via pxe"""
        print "\n\n=================[ BOOTING VMS OVER NETWORK ]================="

        for vm in configFile['vms']:
        hostname        = vm['hostname']
                vmService       = session.system_service().vms_service()
                machine         = vmService.list(search='name=%s' % str(hostname))[0]
        startService    = vmService.vm_service(machine.id)


        startService.start(
                vm=types.Vm(
                os=types.OperatingSystem(
                    boot=types.Boot(
                    devices=[
                            types.BootDevice.NETWORK,
                            types.BootDevice.CDROM
                        ]
                    )
                )
                )
        )
        print "Booting \"%s\"." % (hostname)

def printInformation(session):
    """ Prints out Information about all created virtual machines """

    print "\n\n=================[ VIRTUAL MACHINES ]=================\n"

    table_data        = [['VM', 'CLUSTER','TEMPLATE', 'STORAGE DOMAIN', 'MEMORY', 'DISKS', 'INTERFACES']]

    for vm in configFile['vms']:
        hostname        = vm['hostname']
        cluster        = vm['cluster']
        template    = vm['template']
        storageDomain    = vm['storage-domain']
        memory        = vm['memory']
        diskInfo    = ""
        nicInfo        = ""

        for disk in vm['disks']:
            diskSize        = vm['disks'][disk]
            diskInfo    += disk +" (" + str(diskSize) + " GB)\n"

        for nic in vm['interfaces']:
                    network        = vm['interfaces'][nic]
            nicInfo        += network + " (" + nic + ")\n"

        table_data      += [[ hostname, cluster, template, storageDomain, str(memory) + " GB", diskInfo, nicInfo ]]

    table = SingleTable(table_data)
    table.inner_row_border = True
    table.justify_columns = {0: 'center' , 1: 'center', 2: 'center',3 : 'center',
                 4: 'center', 5: 'center', 6 : 'center'}
    print table.table

def systemExit(code, msgs=None):
    """ Exit with a code and optional message(s). Saved a few lines of code.  """
    if msgs:
        if type(msgs) not in [type([]), type(())]:
            msgs = (msgs, )
        for msg in msgs:
            sys.stderr.write(str(msg) + '\n')
    sys.exit(code)

def main():
        try:
            args = parseArgs()
    except KeyboardInterrupt:
                systemExit(0, "\nUser interrupted process.")

if __name__ == '__main__':
    try:
            sys.exit(abs(main() or 0))
        except KeyboardInterrupt:
            systemExit(0, "\nUser interrupted process.")
