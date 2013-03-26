from sqlalchemy.schema import MetaData, Table, Column, ForeignKey
from sqlalchemy.types import String, Text, DateTime

meta = MetaData()

session = Table('session', meta,
                Column('id', String(32), primary_key=True),
                Column('environment_id', String(32),
                       ForeignKey('environment.id')),
                Column('created', DateTime, nullable=False),
                Column('updated', DateTime, nullable=False),
                Column('user_id', String(32), nullable=False),
                Column('state', Text(), nullable=False),
                )


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    meta.reflect()
    session.create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    session.drop()
