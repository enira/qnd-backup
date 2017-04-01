
from datetime import datetime
import datetime

from database import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True)
    queue = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(64))

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
    __tablename__ = 'pools'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    hosts = db.relationship('Host')

class Host(db.Model):
    __tablename__ = 'hosts'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    password = db.Column(db.String)
    address = db.Column(db.String)
    type = db.Column(db.String)

    pool_id = db.Column(db.Integer, db.ForeignKey('pools.id'))
    pool = db.relationship('Pool', back_populates='hosts')

class Datastore(db.Model):
    """
    A datastore object
    """
    __tablename__ = 'datastores'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    username = db.Column(db.String)
    password = db.Column(db.String)
    host = db.Column(db.String)
    type = db.Column(db.String)                         # only supported type at the moment: smb
    arguments = db.Column(db.String)


class Task(db.Model):
    """
    A task is a one time backup shot. For a scheduled backup, see Schedule
    """
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String)                                                 # uuid of VM to backup
    started = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    ended = db.Column(db.DateTime)
    snapshotname = db.Column(db.String)
    pct1 = db.Column(db.Integer)                                                # first percentage          (0 to 1)
    pct2 = db.Column(db.Integer)                                                # second percentage         (0 to 1)
    divisor = db.Column(db.Integer)                                             # division of percentage    (0 to 1)

    status = db.Column(db.String)

    schedule_id = db.Column(db.Integer)

    datastore_id = db.Column(db.Integer, db.ForeignKey('datastores.id'))
    datastore = db.relationship('Datastore')

    pool_id = db.Column(db.Integer, db.ForeignKey('pools.id'))
    pool = db.relationship('Pool')

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


class Schedule(db.Model):
    """
    A cron like schedule. Picked up by the application flow, and spawns a Task when triggered
    """
    __tablename__ = 'schedules'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    minute = db.Column(db.Integer)
    hour = db.Column(db.Integer)
    day = db.Column(db.Integer)
    month = db.Column(db.Integer)
    week = db.Column(db.Integer)

    uuid = db.Column(db.String(32))                                         # uuid of VM to backup

    datastore_id = db.Column(db.Integer, db.ForeignKey('datastores.id'))
    datastore = db.relationship('Datastore')

    copies = db.Column(db.Integer)                                          # 0 is infinite

class Archive(db.Model):
    """
    Archives are defined by a source datastore, a target datastore and a password to encrypt the backups
    transferred to the target datastore.
    """
    __tablename__ = 'archives'
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('datastores.id'))
    source = db.relationship('Datastore', foreign_keys=[source_id])
    
    target_id = db.Column(db.Integer, db.ForeignKey('datastores.id'))
    target = db.relationship('Datastore', foreign_keys=[target_id])

    encryption_key = db.Column(db.String)

    retention = db.Column(db.Integer) 
    incremental = db.Column(db.Integer) 

class Backup(db.Model):
    """
    A database model spawned after a task has completed a backup.
    """
    __tablename__ = 'backups'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    task = db.relationship('Task')
    metafile = db.Column(db.String)
    backupfile = db.Column(db.String)
    comment = db.Column(db.String)

class Setting(db.Model):
    """
    Application settings.
    """
    __tablename__ = 'settings'
    key = db.Column(db.String, primary_key=True)
    value = db.Column(db.String)