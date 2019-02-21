# rhev-create-vm
Python tool to create virtual machines on RHEV using Rest-API

# Getting Statted
## Dependencies

[Python terminal tables](https://pypi.org/project/terminaltables/)

```
subscription-manager repos --enable=rhel-7-server-rpms
subscription-manager repos --enable=rhel-7-server-rhv-4.1-rpms
yum install python-ovirt-engine-sdk4
```

## Installation
```
git clone hhttps://github.com/FalcoSuessgott/rhev-create-vm
```

## Prerequisites
Create a JSON-File which has the following mandatory fields:

```
{
    "rhevm"     : "hostname-fqdn",
    "profile"   : "profile",
    "ca_file"   : "ca.pem",
    "vms"       : [
        {"hostname"     : "rest-api-1.int",
        "cluster"       : "Default",
        "template"      : "Blank",
        "storage-domain": "storage-domain",
        "memory"        : 5,
        "disks"         : {
            "rest-api-1.sys"    :  30
        },
        "interfaces"    : {
            "nic1"    : "network1",
            "nic2"    : "network2"
            }
        },
 
        {"hostname"     : "rest-api-2.int",
        "cluster"       : "Default",
        "template"      : "Blank",
        "storage-domain": "storage-domain",
        "memory"        : 5,
        "disks"         : {
            "rest-api-2.sys" : 35
        },
        "interfaces"    : {
            "nic1"  : "network2",
            "nic2"  : "network3"
            }
        }
    ]
}
```

In order to authenticate at the rhevm you will need a ca-file. Usually you get this ca-file under /etc/pki/ovirt-engine/ on the rhevm.

## Usage
```
[user:host]$ sudo python rhev-create-vm -c example.json
Password:
=================[ AUTHENTICATING TO RHEVM ]=================
Connecting to "https://rhevmint/ovirt-engine/api" as "user@profile".


=================[ CREATING VMS ]=================
Created VM "rest-api-1.int" on cluster "Default" with template "Blank".
Created VM "rest-api-2.int" on cluster "Default" with template "Blank".


=================[ ADDING NICS ]=================
Adding logical network "network1" to "rest-api-1.int" as NIC "nic1".
Adding logical network "network2" to "rest-api-1.int" as NIC "nic5".
Adding logical network "network2" to "rest-api-2.int" as NIC "nic1".
Adding logical network "network3" to "rest-api-2.int" as NIC "nic5".


=================[ ADDING DISK ]=================
Adding Disk "rest-api-1.sys" with 30 Gb to "rest-api-1.int".
	Waiting for Disk to come up...
	Disk ready.
Adding Disk "rest-api-2.sys" with 35 Gb to "rest-api-2.int".
	Waiting for Disk to come up...
	Disk ready.


=================[ BOOTING VMS OVER NETWORK ]=================
Booting "rest-api-1.int".
Booting "rest-api-2.int".


=================[ VIRTUAL MACHINES ]=================

┌─────────────────────────┬─────────┬──────────┬────────────────────┬────────┬──────────────────────────────┬───────────────────┐
│            VM           │ CLUSTER │ TEMPLATE │   STORAGE DOMAIN   │ MEMORY │            DISKS             │     INTERFACES    │
├─────────────────────────┼─────────┼──────────┼────────────────────┼────────┼──────────────────────────────┼───────────────────┤
│ rest-api-1.int          │ Default │  Blank   │ storage-domain     │  5 GB  │ rest-api-1.sys (30 GB)       │ network1(nic1)    │
│                         │         │          │                    │        │                              │ netowrk2(nic2)    │
│                         │         │          │                    │        │                              │                   │
├─────────────────────────┼─────────┼──────────┼────────────────────┼────────┼──────────────────────────────┼───────────────────┤
│ rest-api-2.int          │ Default │  Blank   │ storage-domain     │  5 GB  │ rest-api-2.sys (35 GB)       │ network2 (nic1)   │
│                         │         │          │                    │        │                              │ network3 (nic2)   │
│                         │         │          │                    │        │                              │                   │
└─────────────────────────┴─────────┴──────────┴────────────────────┴────────┴──────────────────────────────┴───────────────────┘

```


