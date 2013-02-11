from sqlalchemy.schema import MetaData, Table, Column, ForeignKey
from sqlalchemy.types import Integer, String, Text, DateTime


meta = MetaData()

Table('datacenter', meta,
    Column('id', String(32), primary_key=True),
    Column('name', String(255)),
    Column('type', String(255)),
    Column('version', String(255)),
    Column('KMS', String(80)),
    Column('WSUS', String(80)),
    Column('extra', Text()),
)

Table('service', meta,
    Column('id', String(32), primary_key=True),
    Column('datacenter_id', String(32), ForeignKey('datacenter.id')),
    Column('name', String(255)),
    Column('type', String(40)),
    Column('status', String(255)),
    Column('tenant_id', String(40)),
    Column('created_at', DateTime, nullable=False),
    Column('updated_at', DateTime, nullable=False),
    Column('deployed', String(40)),
    Column('vm_id',String(40)),
    Column('extra', Text()),
)



def upgrade(migrate_engine):
    meta.bind = migrate_engine
    meta.create_all()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    meta.drop_all()
