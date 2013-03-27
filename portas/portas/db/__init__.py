from oslo.config import cfg

sql_connection_opt = cfg.StrOpt('sql_connection',
                                default='sqlite:///portas.sqlite',
                                secret=True,
                                metavar='CONNECTION',
                                help='A valid SQLAlchemy connection '
                                     'string for the metadata database. '
                                     'Default: %(default)s')

CONF = cfg.CONF
CONF.register_opt(sql_connection_opt)
