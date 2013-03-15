from sqlalchemy.schema import MetaData, Table, Column
from sqlalchemy.types import String

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    status = Table('status', meta, autoload=True)
    entity_id = Column('entity_id', String(32), nullable=True)
    entity_id.create(status)


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    status = Table('status', meta, autoload=True)
    status.c.entity_id.drop()
