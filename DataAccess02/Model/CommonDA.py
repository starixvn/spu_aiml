from mysql.connector import MySQLConnection
from Configuration.Configuration import config
class CommonDA:
    def __init__(self, sepcific_db):
        self.conn = MySQLConnection(user=sepcific_db.user, password=sepcific_db.pwd,
                                    host=sepcific_db.host, port=sepcific_db.port, database=sepcific_db.database)
        self.cursor = self.conn.cursor()

    def __del__(self):
        self.cursor.close()
        self.conn.close()