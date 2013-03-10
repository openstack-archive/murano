from sqlalchemy.schema import MetaData, Table, Column, ForeignKey
from sqlalchemy.types import String, Text, DateTime

meta = MetaData()

status = Table('status', meta,
               Column('id', String(32), primary_key=True),
               Column('created', DateTime, nullable=False),
               Column('updated', DateTime, nullable=False),
               Column('entity', String(10), nullable=False),
               Column('environment_id', String(32), ForeignKey('environment.id')),
               Column('session_id', String(32), ForeignKey('session.id')),
               Column('text', Text(), nullable=False),
)


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    meta.reflect()
    status.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    status.drop()
