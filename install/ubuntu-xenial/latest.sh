!#/bin/bash

# install from
# wget -O - https://raw.githubusercontent.com/enira/qnd-backup/install/deploy/ubuntu-xenial/latest.sh | sudo bash

# update operating system
apt-get update
apt-get -y upgrade

# install all needed packages
apt-get -y install python python-pip build-essential libssl-dev libffi-dev python-dev git nginx unzip wget

# install postgres
apt-get -y install postgresql postgresql-contrib

# create the database
runuser -l postgres -c $'psql -c "CREATE USER qnd WITH PASSWORD \'quickndirty\';"'
runuser -l postgres -c $'psql -c "CREATE DATABASE qnd OWNER qnd;"'

# check from git the latest commit
mkdir -p /opt/qndbackup/

# download latest 
wget https://github.com/enira/qnd-backup/archive/master.zip -O /opt/qndbackup/latest.zip
unzip /opt/qndbackup/latest.zip -d /opt/qndbackup/
rm /opt/qndbackup/latest.zip
mv /opt/qndbackup/qnd-backup-master/qnd /opt/qndbackup/qnd

# install requirements
pip install -r /opt/qndbackup/qnd/requirements.txt 

# move nginx file
mv /opt/qndbackup/qnd-backup-master/install/ubuntu-xenial/nginx.conf /etc/nginx/nginx.conf

# starting nginx
systemctl restart nginx

# on boot 
systemctl enable nginx

# chown folder
chown -R qnd:qnd /opt/qndbackup/qnd/

# create a log folder for the service 
mkdir -p /var/log/qndbackup/
chown qnd:qnd /var/log/qndbackup/
mv /opt/qndbackup/qnd-backup-master/install/ubuntu-xenial/qndbackup.service /etc/systemd/system/qndbackup.service

# reset the database
python /opt/qndbackup/qnd/reset_db.py

systemctl start qndbackup
systemctl enable qndbackup

rm -rf /opt/qndbackup/qnd-backup-master
