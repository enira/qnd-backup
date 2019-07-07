import os
import configparser

import logging.config
log = logging.getLogger(__name__)

from xen.bridge import Bridge

from xen.types import MessageType, TaskType

from database import db
from database.models import BackupTask, ArchiveTask, RestoreTask, Backup

class Mover:
    """
    Mover class, moves a VM backup from a datastore to an archive
    """
    _server = None

    ARCHIVEROOT = '/media/.qnd'

    def __init__(self):
        # checking if mover is external
        if os.path.isfile('config.ini'):
            # load the external mover
            config = configparser.ConfigParser()
            config.read('config.ini')
            self._server=[config['mover']['hostname'], config['mover']['username'], config['mover']['password']]
        else:
            if os.path.isfile('config.cfg'):
                # load the external mover
                config = configparser.ConfigParser()
                config.read('config.cfg')
                self._server=[config['mover']['hostname'], config['mover']['username'], config['mover']['password']]
            else:
                print('No mover found, archiving not possible.')
                exit()



    #ef update_pct(self, task, pct1, pct2, divisor, status, session)
    def update_pct(self, type, task_id, pct1, pct2, divisor, status, message, id):
        """
        Update percentages for a given task
        """
        session = db.session
        if type == TaskType.ARCHIVE:
            task = session.query(ArchiveTask).filter(ArchiveTask.id == task_id).one()

        task.pct1 = pct1
        if pct2 != None:
            task.pct2 = pct2
        task.divisor = divisor

        task.message = message
        task.status = status
        session.add(task)
        session.commit()

        self._flow.edit_message(id, message, str(int(round(task.pct() *100,0))) , None)

        session.close()

    def delete_reference(self, session, backup_id):
        """
        Deleting all reference tasks.
        """
        tasks = session.query(ArchiveTask).filter(ArchiveTask.backup_id == backup_id).all()
        for task in tasks:
            task.backup = None
            session.add(task)
            session.commit()

        tasks = session.query(BackupTask).filter(BackupTask.backup_id == backup_id).all()
        for task in tasks:
            task.backup = None
            session.add(task)
            session.commit()

        tasks = session.query(RestoreTask).filter(RestoreTask.backup_id == backup_id).all()
        for task in tasks:
            task.backup = None
            session.add(task)
            session.commit()    

    def archive(self, task_id):
        """
        Archive a VM.
        """
        print('Archiving')

        session = db.session
        # get backup object 
        task = session.query(ArchiveTask).filter(ArchiveTask.id == task_id).one()
        taskid = task.id 

        fromds = self.ARCHIVEROOT + '/ds-' + str(task.archive.source.id)
        tods = self.ARCHIVEROOT + '/ds-' + str(task.archive.target.id)

        from_host = task.archive.source.host
        to_host = task.archive.target.host

        from_ds_username = task.archive.source.username
        from_ds_password = task.archive.source.password
        from_ds_host = task.archive.source.host
        from_name = task.archive.source.name

        to_ds_username = task.archive.target.username
        to_ds_password = task.archive.target.password
        to_ds_host = task.archive.target.host
        to_name = task.archive.target.name

        session.close

        self.update_pct(TaskType.ARCHIVE, task_id, 0.10, 0, 0.20, 'ARCHIVE_CONNECTING', messages.ARCHIVE_CONNECTING, taskid)

        if self._server != None:
            connection = Bridge(self._server[0], self._server[1], self._server[2])

            self.update_pct(TaskType.ARCHIVE, task_id, 0.10, 0, 0.20, 'ARCHIVE_MOUNT', messages.ARCHIVE_MOUNT, taskid)

            # create mount points
            connection.sudo_command('mkdir -p ' + fromds, self._server[2])
            connection.sudo_command('mkdir -p ' + tods, self._server[2])

            self.update_pct(TaskType.ARCHIVE, task_id, 0.40, 0, 0.20, 'ARCHIVE_MOUNT', messages.ARCHIVE_MOUNT, taskid)

            # check if wrong mounted
            result = connection.command('df -h | grep -i ' + to_host)
            if len(result) != 0:
                split = result[0].split(' ')
                if split[len(split) - 1] != fromds:
                    result = connection.sudo_command('umount '+ split[len(split) - 1], self._server[2])

            result = connection.command('df -h | grep -i ' + from_host)
            if len(result) != 0:
                split = result[0].split(' ')
                if split[len(split) - 1] != tods:
                    result = connection.sudo_command('umount '+ split[len(split) - 1], self._server[2])


            # check if already mounted
            result = connection.command('df -h | grep -i ' + fromds)
            if len(result) == 0:
                # mount smb
                result = connection.sudo_command('mount -t cifs -o username=' + from_ds_username + ',password=' + from_ds_password + ' ' + from_ds_host + ' ' + fromds, self._server[2])
            else:
                # if we have a wrong mount
                if ds_host != result[0].split(' ')[0]:
                    # unmount
                    result = connection.sudo_command('umount '+ fromds, self._server[2])
                    result = connection.sudo_command('mount -t cifs -o username=' + from_ds_username + ',password=' + from_ds_password + ' ' + from_ds_host + ' ' + fromds, self._server[2])
            
            result = connection.command('df -h | grep -i ' + tods)
            if len(result) == 0:
                # mount smb
                result = connection.sudo_command('mount -t cifs -o username=' + to_ds_username + ',password=' + to_ds_password + ' ' + to_ds_host + ' ' + tods, self._server[2])
            else:
                # if we have a wrong mount
                if ds_host != result[0].split(' ')[0]:
                    # unmount
                    result = connection.sudo_command('umount '+ tods, self._server[2])
                    result = connection.sudo_command('mount -t cifs -o username=' + to_ds_username + ',password=' + to_ds_password + ' ' + to_ds_host + ' ' + tods, self._server[2])
        
        

            result = connection.command('df -h | grep -i ' + tods)
            if len(result) == 0:
                log.error('Could not mount the datastore')
                self.update_pct(TaskType.ARCHIVE, task_id, 1, 1, 0.20, 'ARCHIVE_FAILED_MOUNT', messages.ARCHIVE_FAILED_MOUNT + to_name, taskid)

                self._flow.remove_message(taskid)
                self._flow.add_message(MessageType.NOTIFICATION, 'Archive failed' , messages.ARCHIVE_FAILED_MOUNT + to_name, messages.time())

                return

            result = connection.command('df -h | grep -i ' + fromds)
            if len(result) == 0:
                log.error('Could not mount the datastore')
                self.update_pct(TaskType.ARCHIVE, task_id, 1, 1, 0.20, 'ARCHIVE_FAILED_MOUNT', messages.ARCHIVE_FAILED_MOUNT + from_name, taskid)

                self._flow.remove_message(taskid)
                self._flow.add_message(MessageType.NOTIFICATION, 'Backup failed' , messages.ARCHIVE_FAILED_MOUNT + from_name, messages.time())

                return
            
            session = db.session
            # get backup object 
            task = session.query(ArchiveTask).filter(ArchiveTask.id == task_id).one()
            file = task.backup.backupfile
            # check if file is there 0: is there
            result = command.command('ls -ltr ' + fromds + '/' + file)

            if len(result) == 0:
                log.error('File does not exists')
                cpb = task.backup
                task.backup = None
                self.delete_reference(session, cpb.id)
                session.delete(cpb)
                session.commit()
                
                self.update_pct(TaskType.ARCHIVE, task_id, 1, 1, 0.20, 'ARCHIVE_FAILED_NOTFOUND', messages.ARCHIVE_FAILED_NOTFOUND + task.backup.backupfile, taskid)

                session.close()

                return

            session.close()
            # move file
            result = command.sudo_command('mv ' + fromds + '/' + file + ' ' + tods + '/' + file, self._server[2])

            # check if done
            if len(result) == 4:
                # this is an error
                self.update_pct(TaskType.ARCHIVE, task_id, 1, 1, 0.20, 'ARCHIVE_FAILED_ERROR', messages.ARCHIVE_FAILED_ERROR, taskid)

                return

            # cleanup original task and backup
            session = db.session
            # get backup object 
            task = session.query(ArchiveTask).filter(ArchiveTask.id == task_id).one()

            cpb = task.backup
            task.backup = None
            self.delete_reference(session, cpb.id)
            session.delete(cpb)
            session.commit()

            session.close()

            self.update_pct(task, 0.10, 0, 0.20, 'ARCHIVE_DONE', session)

        else:
            self.update_pct(task, 0.10, 0, 0.20, 'ARCHIVE_FAILED_NOSERVER', session)

        


    def test_host(self, server, username, password):
        """
        OBSOLETE: testing if a host can be connected.
        """
        test = Bridge(server, username, password)
        result = test.command('echo ...')

        try:
            if result[0] == '...':
                return True
            return False
        except:
            return False

    def test_datastore(self, server, username, password):
        """
        OBSOLETE: Testing if a datastore can be connected.
        """

        try:
            if self._server != None:
                m = Bridge(self._server[0], self._server[1], self._server[2])

                folder = self.ARCHIVEROOT + '/test'

                # create mount point
                m.sudo_command('mkdir -p ' + folder, self._server[2])
       
                # check if already mounted
                result = m.command('df -h | grep -i ' + folder)
                if len(result) != 0:
                    # unmount smb
                    m.sudo_command('umount ' + folder, self._server[2])

                    result = m.command('df -h | grep -i ' + folder)
                    if len(result) != 0:
                        # still mounted, issue
                        return False

                # mount
                result = m.sudo_command('mount -t cifs -o username=' + username + ',password=' + password + ' ' + server + ' ' + folder, self._server[2])

                result = m.command('df -h | grep -i ' + folder)
                if len(result) == 0:
                    log.error('Could not mount the datastore')
                    # no datastore mounted
                    return False
                else:
                    # server in datastore
                    if server in result[0] :
                        return True
                    else:
                        # server not mounted
                        return False

            # else fail
            return False
        except:
            # error couldn't mount
            return False