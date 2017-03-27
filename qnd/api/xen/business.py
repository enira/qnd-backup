from database import db
from database.models import Pool, Host, Datastore, Task


# Pools
def create_pool(data):
    name = data.get('name')
    pool = Pool(name=name)

    db.session.add(pool)
    db.session.commit()

def update_pool(pool_id, data):
    pool = db.session.query(Pool).filter(Pool.id == pool_id).one()
    pool.name = data.get('name')
  
    db.session.add(pool)
    db.session.commit()

def delete_pool(pool_id):
    pool = db.session.query(Pool).filter(Pool.id == pool_id).one()
    db.session.delete(pool)
    db.session.commit()


# Hosts 
def create_host(data):
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
    host = db.session.query(Host).filter(Host.id == host_id).one()

    db.session.delete(host)
    db.session.commit()

# Datastores 
def create_datastore(data):
    username = data.get('username')
    password = data.get('password')
    name = data.get('name')
    host = data.get('host')
    type = data.get('type')

    datastore = Datastore(name=name, username=username, password=password, host=host, type=type)

    db.session.add(datastore)
    db.session.commit()

def update_datastore(datastore_id, data):
    datastore = db.session.query(Datastore).filter(Datastore.id == datastore_id).one()

    datastore.name = data.get('name')
    datastore.username = data.get('username')
    datastore.password = data.get('password')
    datastore.host = data.get('host')
    datastore.type = data.get('type')
  
    db.session.add(datastore)
    db.session.commit()

def delete_datastore(datastore_id):
    datastore = db.session.query(Datastore).filter(Datastore.id == datastore_id).one()
    db.session.delete(datastore)
    db.session.commit()


# Tasks
def create_task(data):
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
    task = db.session.query(Task).filter(Task.id == task_id).one()

    db.session.delete(task)
    db.session.commit()