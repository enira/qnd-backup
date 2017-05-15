# Introduction
## Background
So yeah, an introduction. How did this start? Sometimes Xen goes... you know bad. I've had my fair share of difficulties with the platform. When Migrating from 6.5 to 7.0 I lost VMs that where running fine.
A few backup scripts and some Pytho ncode later it took off from there. The result you are seeing is some brain fart, spare time and wanting to be productive.

## Where is this going?
The goal of this little project is to provide a free backup for hobbyists and eventually give back something. I got the XenServer hypervisor for free but I haven't found any real "free" backup solutions that satisfy my needs.
So any code, updates and changes will be made according my personal preference and needs for the time being.

# Installation

## Deploy VM package
A pre defined OVA package can be found at: https://github.com/enira/qnd-backup/releases/download/alpha-3/qnd-alpha-3.ova.gz

## Manual install
### Requirements
A simple VM with:
- 512 MB RAM
- 1 CPU
- 6GB HDD: Less will work too, the bare necessities to run your OS is fine
- Ubuntu 16.04 LTS: Sorry guys, I run 16.04 LTS. I have no intention to support 14.04 LTS (it's three years old now) and Centos... maybe. 

### Ubuntu 16.04 LTS

#### Installing latest release
Installing the server can be done by running:
```
wget -O - https://raw.githubusercontent.com/enira/qnd-backup/master/install/ubuntu-xenial/provision.sh | sudo bash
```

#### Installing latest version
```
wget -O - https://raw.githubusercontent.com/enira/qnd-backup/master/install/ubuntu-xenial/latest.sh | sudo bash
```
#### Upgrading
During the alpha phase, there are no upgrades available.


# Usage

## Ubuntu 16.04 LTS
Once the service is installed it can be used like a normal service.
```
sudo service qnd stop
```
```
sudo service qnd start
```
```
sudo service qnd status
```

# Notice - Releases
Any release marked as alpha is unsafe for stable (and or production) use and should be treated as such. They do not contain any validations and are dumb, input is unvalidated. 
During the alpha phase of the project basic functionality is being gathered and developed at a rapid phase. 

Beta versions are stable for use, however they can contain issues and "undocumented features" (bugs). 

You can see in the milestones what I have planned for each release: https://github.com/enira/qnd-backup/milestones