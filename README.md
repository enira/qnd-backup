# About
This piece of software does a few things:
- Backing up XenServer VMs to a SMB share
- Scheduling of VM backups
- Restoring of said VM
- Archival of old VMs

# Installation
If you want to install this piece of software, there are three options. One is to deploy a VM package, this is the most stable version you can have. It's pre-tested in my environment.
This backup software is tested on XenServer 7.0 at the moment. There are plans to upgrade my cluster to 7.1 in the near future. It might work on XenServer 6.5 but I guess the 7.x line would be best. 

##Requirements
This 'advanced script' isn't demanding on requirements. A simple VM with:
- 512 MB RAM
- 1 CPU
- 6GB HDD: Less will work too, the bare necessities to run your OS is fine
- Ubuntu 16.04 LTS: Sorry guys, I run 16.04 LTS. I have no intention to support 14.04 LTS (it's three years old now) and Centos... maybe. 

## Method 1 - Deploy VM package
A pre defined OVA package can be found at: https://github.com/enira/qnd-backup/releases/download/alpha-3/qnd-alpha-3.ova.gz
This is the most easiest way to get the software up and running. The default OS username and password are: 'qnd/quickndirty'.

## Method 2 - Manual install of the latest stable release
Installing the server can be done by running:
```
wget -O - https://raw.githubusercontent.com/enira/qnd-backup/master/install/ubuntu-xenial/provision.sh | sudo bash
```

## Method 3 - Installing latest version
This method is prone to bugs, undocumented features and can potentially break things. However you will always be running the latest version.
```
wget -O - https://raw.githubusercontent.com/enira/qnd-backup/master/install/ubuntu-xenial/latest.sh | sudo bash
```
# Upgrading
During the alpha phase, there will be no upgrades available. 


# Usage

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

# License
Current license is: Attribution-NoDerivatives 4.0 International (CC BY-ND 4.0)
https://creativecommons.org/licenses/by-nd/4.0/

# Small Q & A
## Why did you made this piece of software?
So yeah, how did this all start? Sometimes Xen goes... you know bad. I've had my fair share of difficulties with the platform. When Migrating from 6.5 to 7.0 I lost quite a few VMs that where running fine.
A few backup scripts and some Python code later it took off from there. I just love writing Python code. This Git repository is my way of producting something whil gaining maturity with the platform, language and releases at the same time.

## Why such a restrictive license?
This is the first project I am releasing ever. That's why I am putting this rather restrictive license on it. Because I do not have any experience with this part of releasing software. Perhaps a less restrictive license would be fine as well.
I guess eventually licensing thing will solve itself over time.

## Why the donations in the software?
GitHub be my witness: This software will always be a free backup tool for hobbyists and personal use. I got the XenServer hypervisor for free and this is my way of giving something back. 
There is a simple reason why I am putting donations in there. 99% of all the bugs that are found by other people and that I cannot solve are due to two reasons: a) Very specific environment variables and b) No hardware for me to test on.
E.g.: When I upgrade my cluster from 7.0 to 7.1 or 7.2 this will cease all testing on XenServer 7.0, as I just don't have any budget for an additional cluster to test older XenServer versions. 
Hence the donations, they allow me to expand a little bit and keep my intrest going. 

## Where is this going? 
The goal of this little project is to provide a free backup and I haven't found any real "free" backup solutions that just satisfy my needs. Any code, updates and changes are being made according my personal preference and needs for the time being.
You can also view the issues tab on GitHub: https://github.com/enira/qnd-backup/issues Whenever I have an idea I create a ticket for it.



