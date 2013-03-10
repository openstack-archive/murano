from sqlalchemy.schema import MetaData, Table, Column
from sqlalchemy.types import Text

meta = MetaData()


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    session = Table('session', meta, autoload=True)
    description = Column('description', Text(), nullable=True, default='{}')
    description.create(session)


def downgrade(migrate_engine):
    meta.bind = migrate_engine
    session = Table('session', meta, autoload=True)
    session.c.description.drop()
