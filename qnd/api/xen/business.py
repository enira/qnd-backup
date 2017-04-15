from database import db
from database.models import Pool, Host, Datastore, Task, Archive, Schedule

from xen.flow import Flow

# Pools
def create_pool(data):
    """
    Create a pool. Id is ignored.
    """
    name = data.get('name')
    pool = Pool(name=name)

    db.session.add(pool)
    db.session.commit()

def update_pool(pool_id, data):
    """
    Update a pool
    """
    pool = db.session.query(Pool).filter(Pool.id == pool_id).one()
    pool.name = data.get('name')
  
    db.session.add(pool)
    db.session.commit()

def delete_pool(pool_id):
    """
    Delete a pool.
    """
    pool = db.session.query(Pool).filter(Pool.id == pool_id).one()
    db.session.delete(pool)
    db.session.commit()


# Hosts 
def create_host(data):
    """
    Create a host.
    """
    username = data.get('username')
    password = data.get('password')
    address = data.get('address')
    # type is only used internally
    # type = data.get('type')

    pool_id = data.get('pool_id')
    pool = db.session.query(Pool).filter(Pool.id == pool_id).one()

    host = Host(username=username, password=password, address=address, pool=pool)

    db.session.add(host)
    db.session.commit()

def update_host(host_id, data):
    """
    Update a host.
    """
    host = Host.query.filter(Host.id == host_id).one()

    pool_id = data.get('pool_id')
    pool = db.session.query(Pool).filter(Pool.id == pool_id).one()

    host.username = data.get('username')
    host.password = data.get('password')
    host.address = data.get('address')
    # type is only used internally
    # host.type = data.get('type')
    host.pool = pool

    db.session.add(host)
    db.session.commit()

def delete_host(host_id):
    """
    Delete a host.
    """
    host = db.session.query(Host).filter(Host.id == host_id).one()

    db.session.delete(host)
    db.session.commit()

# Datastores 
def create_datastore(data):
    """
    Create a datastore.
    """
    username = data.get('username')
    password = data.get('password')
    name = data.get('name')
    host = data.get('host')
    type = data.get('type')

    datastore = Datastore(name=name, username=username, password=password, host=host, type=type)

    db.session.add(datastore)
    db.session.commit()

def update_datastore(datastore_id, data):
    """
    Update a datastore.
    """
    datastore = db.session.query(Datastore).filter(Datastore.id == datastore_id).one()

    datastore.name = data.get('name')
    datastore.username = data.get('username')
    datastore.password = data.get('password')
    datastore.host = data.get('host')
    datastore.type = data.get('type')
  
    db.session.add(datastore)
    db.session.commit()

def delete_datastore(datastore_id):
    """
    Delete datastore.
    """
    datastore = db.session.query(Datastore).filter(Datastore.id == datastore_id).one()
    db.session.delete(datastore)
    db.session.commit()


# Tasks
def create_task(data):
    """
    Create a task.
    """
    pool_id = data.get('pool_id')
    pool = db.session.query(Pool).filter(Pool.id == pool_id).one()

    datastore_id = data.get('datastore_id')
    datastore = db.session.query(Datastore).filter(Datastore.id == datastore_id).one()

    status = data.get('status')
    divisor = data.get('divisor')
    pct1 = data.get('pct1')
    pct2 = data.get('pct2')
    uuid = data.get('uuid')

    task = Task(status=status, divisor=divisor, pct1=pct1, pct2=pct2, uuid=uuid, pool=pool, datastore=datastore)

    try:
        db.session.add(task)
        db.session.commit()
    except Exception as e:
        print e

def update_task(task_id, data):
    """
    Update a task.
    """
    task = db.session.query(Task).filter(Task.id == task_id).one()

    pool_id = data.get('pool_id')
    pool = db.session.query(Pool).filter(Pool.id == pool_id).one()

    datastore_id = data.get('datastore_id')
    datastore = db.session.query(Datastore).filter(Datastore.id == datastore_id).one()


    task.status = data.get('status')
    task.divisor = data.get('divisor')
    task.pct1 = data.get('pct1')
    task.pct2 = data.get('pct2')
    task.uuid = data.get('uuid')
    task.pool = pool
    task.datastore = datastore

    db.session.add(task)
    db.session.commit()

def delete_task(task_id):
    """
    Delete a task.
    """
    task = db.session.query(Task).filter(Task.id == task_id).one()

    db.session.delete(task)
    db.session.commit()

# Archives
def create_archive(data):
    """
    Create an archive. Id is ignored.
    """
    source_id = data.get('source_id')
    source = db.session.query(Datastore).filter(Datastore.id == source_id).one()

    target_id = data.get('target_id')
    target = db.session.query(Datastore).filter(Datastore.id == target_id).one()

    encryption_key = data.get('encryption_key')
    retention = data.get('retention')
    incremental = data.get('incremental')
    name = data.get('name')

    archive = Archive(source=source, target=target, encryption_key=encryption_key, retention=retention, incremental=incremental, name=name)

    db.session.add(archive)
    db.session.commit()

def update_archive(archive_id, data):
    """
    Update an archive
    """
    archive = db.session.query(Archive).filter(Archive.id == archive_id).one()

    source_id = data.get('source_id')
    archive.source = db.session.query(Datastore).filter(Datastore.id == source_id).one()

    target_id = data.get('target_id')
    archive.target = db.session.query(Datastore).filter(Datastore.id == target_id).one()

    archive.encryption_key = data.get('encryption_key')
    archive.retention = data.get('retention')
    archive.incremental = data.get('incremental')
    archive.name = data.get('name')
  
    db.session.add(archive)
    db.session.commit()

def delete_archive(archive_id):
    """
    Delete an archive.
    """
    archive = db.session.query(Archive).filter(Archive.id == archive_id).one()
    db.session.delete(archive)
    db.session.commit()

# Schedules
def create_schedule(data):
    """
    Create a schedule. Id is ignored.
    """
    name = data.get('name')
    minute = data.get('minute')
    hour = data.get('hour')
    day = data.get('day')
    month = data.get('month')
    week = data.get('week')
    uuid = data.get('uuid')

    pool_id = data.get('pool_id')
    pool = db.session.query(Pool).filter(Pool.id == pool_id).one()

    datastore_id = data.get('datastore_id')
    datastore = db.session.query(Datastore).filter(Datastore.id == datastore_id).one()

    schedule = Schedule(name=name, minute=minute, hour=hour, day=day, month=month, week=week, uuid=uuid, pool=pool, datastore=datastore)

    db.session.add(schedule)
    db.session.commit()

    Flow.instance().schedule_add(schedule.id)

def update_schedule(schedule_id, data):
    """
    Update a schedule
    """
    schedule = db.session.query(Schedule).filter(Schedule.id == schedule_id).one()

    pool_id = data.get('pool_id')
    schedule.pool = db.session.query(Pool).filter(Pool.id == pool_id).one()

    datastore_id = data.get('datastore_id')
    schedule.datastore = db.session.query(Datastore).filter(Datastore.id == datastore_id).one()

    schedule.name = data.get('name')
    schedule.minute = data.get('minute')
    schedule.hour = data.get('hour')
    schedule.day = data.get('day')
    schedule.month = data.get('month')
    schedule.week = data.get('week')
    schedule.uuid = data.get('uuid')
  
    db.session.add(schedule)
    db.session.commit()

    Flow.instance().schedule_update(schedule.id)

def delete_schedule(schedule_id):
    """
    Delete a schedule.
    """
    schedule = db.session.query(Schedule).filter(Schedule.id == schedule_id).one()
    db.session.delete(schedule)
    db.session.commit()

    Flow.instance().schedule_delete(schedule.id)
