!#/bin/bash

# install from
# wget -O - https://raw.githubusercontent.com/enira/qnd-backup/master/deploy/ubuntu-xenial/provision.sh | sudo bash

apt-get update
apt-get -y upgrade
apt-get -y install python python-pip build-essential libssl-dev libffi-dev python-dev git

mkdir -p /opt/qndbackup/
cd /opt/qndbackup/

git clone https://github.com/enira/qnd-backup.git --depth 1 /opt/qndbackup/
git checkout tags/`git tag`

pip install -r /opt/qndbackup/qnd/requirements.txt

echo "Application installed..."
echo "You can start the application with 'sudo nohup python /opt/qndbackup/qnd/app.py &'"