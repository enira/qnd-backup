from datetime import datetime
import datetime

from database import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)                                    # id
    username = db.Column(db.String(32), index=True)                                 # the username
    password_hash = db.Column(db.String(64))                                        # hashed password

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None    # valid token, but expired
        except BadSignature:
            return None    # invalid token
        user = User.query.get(data['id'])
        return user

class Pool(db.Model):
    """
    A pool is a logical concept containing a grouping of XenServers.
    """
    __tablename__ = 'pools'
    id = db.Column(db.Integer, primary_key=True)                                # id
    name = db.Column(db.String)                                                 # name of the pool
    hosts = db.relationship('Host')                                             # associated hosts

class Host(db.Model):
    """
    A host is associated with a pool and contains credentials of one XenServer.
    """
    __tablename__ = 'hosts'
    id = db.Column(db.Integer, primary_key=True)                                # id
    username = db.Column(db.String)                                             # username
    password = db.Column(db.String)                                             # password
    address = db.Column(db.String)                                              # host IP address or hostname
    type = db.Column(db.String)                                                 # type - not used

    pool_id = db.Column(db.Integer, db.ForeignKey('pools.id'))                  # associated pool id
    pool = db.relationship('Pool', back_populates='hosts', lazy='immediate')                      # associated pool object

class Datastore(db.Model):
    """
    A datastore object
    """
    __tablename__ = 'datastores'
    id = db.Column(db.Integer, primary_key=True)                                # id
    name = db.Column(db.String)                                                 # identification name
    username = db.Column(db.String)                                             # username
    password = db.Column(db.String)                                             # password
    host = db.Column(db.String)                                                 # host IP address or hostname
    type = db.Column(db.String)                                                 # only supported type at the moment: smb
    arguments = db.Column(db.String)                                            # unsupported


class Schedule(db.Model):
    """
    A cron like schedule. Picked up by the application flow, and spawns a Task when triggered
    """
    __tablename__ = 'schedules'
    id = db.Column(db.Integer, primary_key=True)                                # id
    name = db.Column(db.String)                                                 # schedule name

    minute = db.Column(db.String)                                               # cron - minute of hour
    hour = db.Column(db.String)                                                 # cron - hour of day
    day = db.Column(db.String)                                                  # cron - day of month
    month = db.Column(db.String)                                                # cron - month
    week = db.Column(db.String)                                                 # cron - weekday
    uuid = db.Column(db.String)                                                 # uuid of VM to backup
    datastore_id = db.Column(db.Integer, db.ForeignKey('datastores.id'))        # datastore id
    datastore = db.relationship('Datastore', lazy='immediate')                                    # datastore object  
    pool_id = db.Column(db.Integer, db.ForeignKey('pools.id'))                  # pool id
    pool = db.relationship('Pool', lazy='immediate')                                              # pool object


class Archive(db.Model):
    """
    Archives are defined by a source datastore, a target datastore and a password to encrypt the backups
    transferred to the target datastore.
    """
    __tablename__ = 'archives'
    id = db.Column(db.Integer, primary_key=True)                                # id
    name = db.Column(db.String)                                                 # the display name

    source_id = db.Column(db.Integer, db.ForeignKey('datastores.id'))           # datastore id
    source = db.relationship('Datastore', foreign_keys=[source_id], lazy='immediate')             # datastore object  
    
    target_id = db.Column(db.Integer, db.ForeignKey('datastores.id'))           # datastore id
    target = db.relationship('Datastore', foreign_keys=[target_id], lazy='immediate')             # datastore object  

    encryption_key = db.Column(db.String)                                       # encryption key 

    retention = db.Column(db.Integer)                                           # amount of backups to keep before archiving  
    incremental = db.Column(db.Integer)                                         # not implemented



class Setting(db.Model):
    """
    Application settings. Key value pair store.
    """
    __tablename__ = 'settings'
    key = db.Column(db.String, primary_key=True)                                # key
    value = db.Column(db.String)                                                # value



class Backup(db.Model):
    """
    A database model spawned after a task has completed a backup.
    """
    __tablename__ = 'backups'
    id = db.Column(db.Integer, primary_key=True)                                # id
    metafile = db.Column(db.String)                                             # meta-file location
    backupfile = db.Column(db.String)                                           # backup file location
    snapshotname = db.Column(db.String)                                         # name of the snapshot

    comment = db.Column(db.String)                                              # comments on the backup
    uuid = db.Column(db.String)                                                 # uuid of VM to backup

    datastore_id = db.Column(db.Integer, db.ForeignKey('datastores.id'))        # datastore id
    datastore = db.relationship('Datastore', lazy='immediate')                                    # datastore object  
    pool_id = db.Column(db.Integer, db.ForeignKey('pools.id'))                  # pool id
    pool = db.relationship('Pool', lazy='immediate')                                              # pool object


class BackupTask(db.Model):
    """
    A task is a one time backup shot. For a scheduled backup, see Schedule
    """
    __tablename__ = 'backuptasks'
    id = db.Column(db.Integer, primary_key=True)                                # id

    schedule_id = db.Column(db.Integer)                                         # if there is an associated schedule
    

    backup_id = db.Column(db.Integer, db.ForeignKey('backups.id'))              # backup id
    backup = db.relationship('Backup', lazy='immediate')                        # backup object

    #duplicate
    uuid = db.Column(db.String)                                                 # uuid of VM to backup
    datastore_id = db.Column(db.Integer, db.ForeignKey('datastores.id'))        # datastore id
    pool_id = db.Column(db.Integer, db.ForeignKey('pools.id'))                  # pool id

    started = db.Column(db.DateTime, default=datetime.datetime.utcnow)          # start time
    ended = db.Column(db.DateTime)                                              # end time

    pct1 = db.Column(db.Integer)                                                # first percentage          (0 to 1)
    pct2 = db.Column(db.Integer)                                                # second percentage         (0 to 1)
    divisor = db.Column(db.Integer)                                             # division of percentage    (0 to 1)

    status = db.Column(db.String)                                               # status of the task
    def pct(self):
        if self.pct1 == None:
            s1 = 0
        else:
            s1 = self.pct1

        if self.pct2 == None:
            s2 = 0
        else:
            s2 = self.pct1

        if self.divisor == None:
            d = 1
        else:
            d = self.divisor

        return s1 * d + s2 * (1 - d)

class ArchiveTask(db.Model):
    __tablename__ = 'archivetasks'
    id = db.Column(db.Integer, primary_key=True)                                # id

    started = db.Column(db.DateTime, default=datetime.datetime.utcnow)          # start time
    ended = db.Column(db.DateTime)                                              # end time

    archive_id = db.Column(db.Integer, db.ForeignKey('archives.id'), nullable=True)                  # task id
    archive = db.relationship('Archive', lazy='immediate')                                              # task object

    backup_id = db.Column(db.Integer, db.ForeignKey('backups.id'), nullable=True)                  # task id
    backup = db.relationship('Backup', lazy='immediate')                                              # task object


    pct1 = db.Column(db.Integer)                                                # first percentage          (0 to 1)
    pct2 = db.Column(db.Integer)                                                # second percentage         (0 to 1)
    divisor = db.Column(db.Integer)                                             # division of percentage    (0 to 1)

    status = db.Column(db.String)                                               # status of the task
    def pct(self):
        if self.pct1 == None:
            s1 = 0
        else:
            s1 = self.pct1

        if self.pct2 == None:
            s2 = 0
        else:
            s2 = self.pct1

        if self.divisor == None:
            d = 1
        else:
            d = self.divisor

        return s1 * d + s2 * (1 - d)

class RestoreTask(db.Model):
    """
    A task is a one restore.
    """
    __tablename__ = 'restoretasks'
    id = db.Column(db.Integer, primary_key=True)                                # id
    started = db.Column(db.DateTime, default=datetime.datetime.utcnow)          # start time
    ended = db.Column(db.DateTime)                                              # end time
    backupname = db.Column(db.String)                                         # name of the xva

    backup_id = db.Column(db.Integer, db.ForeignKey('backups.id'))              # backup id
    backup = db.relationship('Backup', lazy='immediate')                        # backup object

    pct1 = db.Column(db.Integer)                                                # first percentage          (0 to 1)
    pct2 = db.Column(db.Integer)                                                # second percentage         (0 to 1)
    divisor = db.Column(db.Integer)                                             # division of percentage    (0 to 1)

    status = db.Column(db.String)                                               # status of the task
    def pct(self):
        if self.pct1 == None:
            s1 = 0
        else:
            s1 = self.pct1

        if self.pct2 == None:
            s2 = 0
        else:
            s2 = self.pct1

        if self.divisor == None:
            d = 1
        else:
            d = self.divisor

        return s1 * d + s2 * (1 - d)
