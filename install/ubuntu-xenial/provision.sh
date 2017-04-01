!#/bin/bash

# install from
# wget -O - https://raw.githubusercontent.com/enira/qnd-backup/install/deploy/ubuntu-xenial/provision.sh | sudo bash

# update operating system
apt-get update
apt-get -y upgrade

# install all needed packages
apt-get -y install python python-pip build-essential libssl-dev libffi-dev python-dev git nginx unzip

# check from git the latest release
mkdir -p /opt/qndbackup/
echo "Downloading release: `git ls-remote --tags https://github.com/enira/qnd-backup.git | awk -F/ '{print $NF}' | tail -1`"

# download latest release
wget https://github.com/enira/qnd-backup/archive/`git ls-remote --tags https://github.com/enira/qnd-backup.git | awk -F/ '{print $NF}' | tail -1`.zip -O /opt/qndbackup/release.zip
unzip /opt/qndbackup/release.zip -d /opt/qndbackup/
rm /opt/qndbackup/release.zip
mv /opt/qndbackup/qnd-backup-`git ls-remote --tags https://github.com/enira/qnd-backup.git | awk -F/ '{print $NF}' | tail -1`/qnd /opt/qndbackup/qnd

# install requirements
pip install -r /opt/qndbackup/qnd/requirements.txt 

# move nginx file
mv /opt/qndbackup/qnd-backup-`git ls-remote --tags https://github.com/enira/qnd-backup.git | awk -F/ '{print $NF}' | tail -1`/install/ubuntu-xenial/nginx.conf /etc/nginx/nginx.conf

# starting nginx
systemctl restart nginx

# on boot 
systemctl enable nginx

# create a log folder for the service 
mkdir -p /var/log/qnd/
chown qnd:qnd /var/log/qnd/
mv /opt/qndbackup/qnd-backup-`git ls-remote --tags https://github.com/enira/qnd-backup.git | awk -F/ '{print $NF}' | tail -1`/install/ubuntu-xenial/qnd.service /etc/systemd/system/qnd.service

systemctl start qnd
systemctl enable qnd

rm -rf /opt/qndbackup/qnd-backup-`git ls-remote --tags https://github.com/enira/qnd-backup.git | awk -F/ '{print $NF}' | tail -1`