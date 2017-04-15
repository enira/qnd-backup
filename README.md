# Introduction
## Background
So yeah, an introduction. How did this start? Sometimes Xen goes... bad. I've had my fair share of difficulties with the platform. However I am running a small home lab on Intel NUCs with not much memory. 
On such a setup XenServer simply rocks. KVM and QEMU are too high maintenance, vSphere with vCenter is just too bloaty. 
One Monday evening I experienced one of those undocumented Xen oddities and lost a VM which I haven't backed up... oops. The urge really started to build up to actually do something with backing up my home lab, and do it in a consistent scheduled way.
Eventually a few days later (Thursday evening) I started writing Python code to actually backup VMs in my environment. By Firday evening, before going to the pub, I started working on the REST API and by Sunday I loaded a Bootstrap template I found somewhere.
Hence the name: 'Quick 'n Dirty'.

## Where is this going?
During the week after I build a very rough 'advanced backup script' I started to realize: all this effort I spent in this eventually will simply go to waste, so I am uploading everything to github with the hopes somewhere and somehow this effort will help save a VM somewhere.
The project itself is at the moment not mature in any way. And it will take quite a while to do so. It might just all stop if there is no interest 

# Installation
## Requirements
A simple VM with:
- 512 MB RAM
- 1 CPU
- 6GB HDD: Less will work too, the bare necessities to run your OS is fine
- Ubuntu 16.04 LTS: Sorry guys, I run 16.04 LTS. I have no intention to support 14.04 LTS (it's three years old now) and Centos... maybe. 

## Ubuntu 16.04 LTS

### Installing latest release
Installing the server can be done by running:
```
wget -O - https://raw.githubusercontent.com/enira/qnd-backup/master/install/ubuntu-xenial/provision.sh | sudo bash
```

### Installing latest version
```
wget -O - https://raw.githubusercontent.com/enira/qnd-backup/master/install/ubuntu-xenial/latest.sh | sudo bash
```
### Upgrade 
TODO




# Usage
```
sudo service
```
## Ubuntu 16.04 LTS


# Notice - Release: alpha-2
The alpha-2 release is not yet thoroughly bug tested. Expect to run into issues at one point. It is only the second iteration of these code, trying to stick to a few release versions with each added functionality and enhancement for previous added functionality. You can see in the milestones what I have planned for each release: https://github.com/enira/qnd-backup/milestones

