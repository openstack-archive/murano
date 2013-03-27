from sqlalchemy.schema import MetaData, Table, Column, ForeignKey
from sqlalchemy.types import String, Text, DateTime


meta = MetaData()

service = Table('service', meta,
                Column('id', String(32), primary_key=True),
                Column('name', String(255), nullable=False),
                Column('type', String(40), nullable=False),
                Column('environment_id', String(32),
                       ForeignKey('environment.id')),
                Column('created', DateTime, nullable=False),
                Column('updated', DateTime, nullable=False),
                Column('description', Text(), nullable=False),
                )


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    meta.reflect()
    service.drop()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    meta.reflect()
    service.create()
