from mysql.connector import MySQLConnection
from mysql.connector.pooling import MySQLConnectionPool
from Configuration.Configuration import config


class CommonDA:
    def create_pool(sepcific_db):
        pool = MySQLConnectionPool(pool_name=config.pool_name, pool_size=config.pool_size,
                                   user=sepcific_db.user, password=sepcific_db.pwd, host=sepcific_db.host, port=sepcific_db.port, database=sepcific_db.database, autocommit=True, connection_timeout = 1000)
        return pool

    def single_connection(sepcific_db):
        conn = MySQLConnection(
            user=sepcific_db.user, password=sepcific_db.pwd, host=sepcific_db.host, port=sepcific_db.port, database=sepcific_db.database, autocommit=True, connection_timeout = 1000)
        return conn
